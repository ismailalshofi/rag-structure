import os

from app.models import FileType
from app.models.enums.responses import ResponseMessage
from app.schemas.document import ProcessRequest, ProcessResponse
from app.services.project import ProjectService

from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ProcessingService:

    @staticmethod
    def get_file_extension(file_id: str) -> str:
        return os.path.splitext(file_id)[-1]

    @staticmethod
    def get_file_loader(file_id: str, project_path: str):
        extension = ProcessingService.get_file_extension(file_id)
        file_path = os.path.join(project_path, file_id)

        if extension == FileType.TEXT.value:
            return TextLoader(file_path=file_path, encoding='utf-8')

        elif extension == FileType.PDF.value:
            return PyMuPDFLoader(file_path=file_path)

        return None

    @staticmethod
    def chunk_content(content: list, chunk_size: int = 100, overlap_size: int = 20):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            length_function=len
        )

        texts = [item.page_content for item in content]
        metadatas = [item.metadata for item in content]

        chunks = text_splitter.create_documents(texts, metadatas)

        return chunks

    @staticmethod
    def to_response(chunks: list, file_id: str) -> ProcessResponse:
        return ProcessResponse(
            file_id=file_id,
            message=ResponseMessage.PROCESSING_SUCCESS.value,
            total_chunks=len(chunks),
            chunks=[
                {"page_content": doc.page_content, "metadata": doc.metadata}
                for doc in chunks
            ]
        )

    @staticmethod
    async def process(project_id: str, request: ProcessRequest) -> ProcessResponse:
        project_path = ProjectService.get_project_path(project_id)

        loader = ProcessingService.get_file_loader(request.file_id, project_path)
        content = loader.load()
        chunks = ProcessingService.chunk_content(content, request.chunk_size, request.overlap_size)

        return ProcessingService.to_response(chunks, request.file_id)
