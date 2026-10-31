import os

import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.models import Chunk, FileType


class ProcessingService:
    """File -> pages of text -> overlapping chunks that keep their page number."""

    @staticmethod
    def get_file_extension(file_id: str) -> str:
        return os.path.splitext(file_id)[-1].lower()

    @staticmethod
    def load_pages(file_path: str) -> list[tuple[int | None, str]]:
        extension = ProcessingService.get_file_extension(file_path)

        if extension == FileType.PDF.value:
            with pymupdf.open(file_path) as pdf:
                return [(number, page.get_text()) for number, page in enumerate(pdf, start=1)]

        if extension in (FileType.TEXT.value, FileType.MARKDOWN.value):
            with open(file_path, encoding="utf-8") as f:
                return [(None, f.read())]

        raise ValueError(f"Unsupported file type: {extension}")

    @staticmethod
    def chunk_pages(pages: list[tuple[int | None, str]], file_id: str, chunk_size: int, overlap: int) -> list[Chunk]:
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        chunks = []
        for page, text in pages:
            for piece in splitter.split_text(" ".join(text.split())):
                chunks.append(Chunk(text=piece, file_id=file_id, chunk_index=len(chunks), page=page))
        return chunks

    @staticmethod
    def process(file_path: str, file_id: str, chunk_size: int, overlap: int) -> list[Chunk]:
        return ProcessingService.chunk_pages(ProcessingService.load_pages(file_path), file_id, chunk_size, overlap)
