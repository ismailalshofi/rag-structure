from abc import ABC, abstractmethod

from openai import OpenAI

from app.config import Settings


class LLMNotConfigured(RuntimeError):
    pass


class LLM(ABC):
    @abstractmethod
    def complete(self, messages: list[dict]) -> str: ...


class OpenAICompatibleLLM(LLM):
    """Any OpenAI-compatible chat API: OpenRouter (default), OpenAI, Groq, Ollama, vLLM..."""

    def __init__(self, api_key: str, base_url: str, model: str, temperature: float = 0.1):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        # Created on first use, so upload and search work without an LLM key
        if self._client is None:
            if not self.api_key:
                raise LLMNotConfigured("LLM_API_KEY is not set. Search works without it, /ask needs it.")
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def complete(self, messages: list[dict]) -> str:
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=self.temperature
        )
        return (response.choices[0].message.content or "").strip()


def create_llm(settings: Settings) -> LLM:
    return OpenAICompatibleLLM(
        settings.LLM_API_KEY, settings.LLM_BASE_URL, settings.LLM_MODEL, settings.LLM_TEMPERATURE
    )
