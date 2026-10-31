from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    file_id: str
    # None uses CHUNK_SIZE / CHUNK_OVERLAP from the settings
    chunk_size: int | None = Field(default=None, ge=100, le=8000)
    overlap: int | None = Field(default=None, ge=0, le=2000)


class IndexResponse(BaseModel):
    message: str
    file_id: str
    total_chunks: int
