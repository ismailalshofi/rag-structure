from collections import deque
from threading import Lock


class ConversationMemory:
    """The last few turns of each chat session, kept in the process.

    Enough for follow-up questions ("and what about tennis?"). It is lost on restart; a real
    deployment would keep it in Redis or the database, behind the same three methods.
    """

    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        self._sessions: dict[str, deque] = {}
        self._lock = Lock()

    def get(self, session_id: str) -> list[dict]:
        with self._lock:
            return list(self._sessions.get(session_id, []))

    def add(self, session_id: str, question: str, answer: str) -> None:
        with self._lock:
            turns = self._sessions.setdefault(session_id, deque(maxlen=self.max_turns))
            turns.append({"question": question, "answer": answer})

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
