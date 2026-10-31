from pydantic import BaseModel, Field

from app.models import SearchHit


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=50)
    file_id: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1)
    # Send the same session_id to ask follow-up questions
    session_id: str | None = None
    top_k: int | None = Field(default=None, ge=1, le=50)
    file_id: str | None = None


class Source(BaseModel):
    number: int
    file_id: str
    page: int | None
    score: float
    text: str

    @classmethod
    def from_hit(cls, number: int, hit: SearchHit) -> "Source":
        c = hit.chunk
        return cls(number=number, file_id=c.file_id, page=c.page, score=round(hit.score, 4), text=c.text)


class SearchResponse(BaseModel):
    results: list[Source]


class AskResponse(BaseModel):
    answer: str
    search_query: str
    grounded: bool
    cited: list[int]
    sources: list[Source]
