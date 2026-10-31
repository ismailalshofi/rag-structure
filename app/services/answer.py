import re
from dataclasses import dataclass, field

from app.models import SearchHit
from app.providers.llm import LLM
from app.services.memory import ConversationMemory
from app.services.retrieval import RetrievalService

NOT_FOUND = "I couldn't find this in the documents."

ANSWER_PROMPT = """You answer questions using only the numbered sources below.
- Cite the sources you used like [1] or [2][3], right after the sentence they support.
- If the sources don't contain the answer, say you couldn't find it in the documents. Don't guess.
- Keep it short and direct.

Sources:
{sources}"""

CONDENSE_PROMPT = """Rewrite the follow-up question so it can be understood without the conversation.
Keep the meaning. Reply with the question only.

Conversation:
{history}

Follow-up question: {question}"""


@dataclass
class Answer:
    answer: str
    # What was actually searched: the question rewritten with the conversation's context
    search_query: str
    sources: list[SearchHit] = field(default_factory=list)
    cited: list[int] = field(default_factory=list)
    grounded: bool = False


class AnswerService:
    def __init__(self, retrieval: RetrievalService, llm: LLM, memory: ConversationMemory, min_score: float):
        self.retrieval = retrieval
        self.llm = llm
        self.memory = memory
        self.min_score = min_score

    def ask(
        self, project_id: str, question: str, top_k: int, session_id: str | None = None, file_id: str | None = None
    ) -> Answer:
        history = self.memory.get(session_id) if session_id else []
        search_query = self._standalone(question, history) if history else question

        hits = [h for h in self.retrieval.search(project_id, search_query, top_k, file_id) if h.score >= self.min_score]
        if not hits:
            # Nothing relevant enough: say so instead of letting the LLM answer from memory
            answer = Answer(NOT_FOUND, search_query)
        else:
            sources = "\n\n".join(f"[{i}] {h.chunk.text}" for i, h in enumerate(hits, start=1))
            messages = [{"role": "system", "content": ANSWER_PROMPT.format(sources=sources)}]
            for turn in history:
                messages += [
                    {"role": "user", "content": turn["question"]},
                    {"role": "assistant", "content": turn["answer"]},
                ]
            messages.append({"role": "user", "content": question})

            text = self.llm.complete(messages)
            cited = sorted({int(n) for n in re.findall(r"\[(\d+)\]", text) if 1 <= int(n) <= len(hits)})
            answer = Answer(text, search_query, hits, cited, grounded=bool(cited))

        if session_id:
            self.memory.add(session_id, question, answer.answer)
        return answer

    def _standalone(self, question: str, history: list[dict]) -> str:
        lines = "\n".join(f"User: {t['question']}\nAssistant: {t['answer']}" for t in history)
        prompt = CONDENSE_PROMPT.format(history=lines, question=question)
        return self.llm.complete([{"role": "user", "content": prompt}]) or question
