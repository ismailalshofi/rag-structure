import os
from app.models import FileType
from app.models.enums.response_enum import ResponseMessage
from app.schema.file import ProcessRequest, ProcessResponse
from app.services.base import BaseService
from app.services.project import ProjectService

from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class ProcessService(BaseService):

    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.project_path = ProjectService().get_project_path(project_id=project_id)

    def get_file_extenstion(self, file_id):
        return os.path.splitext(file_id)[-1]

    def to_json(self, chunks: list, file_id: str):
        json_chunks = [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata
            } for doc in chunks
        ]

        json = {
            "file_id": file_id,
            "message": ResponseMessage.PROCESSING_SUCCESS,
            "total_chunks": len(chunks),
            "chunks": json_chunks
        }
        return json

    def get_file_loader(self, file_id: str):
        
        extension = self.get_file_extenstion(file_id=file_id)
        file_path = os.path.join(
            self.project_path,
            file_id
        ) 

        # 1) Text Loader
        if extension == FileType.TEXT.value:
            return TextLoader(file_path=file_path, encoding='utf-8')
        
        # 2) PDF Loader
        elif extension == FileType.PDF.value:
            return PyMuPDFLoader(file_path=file_path)

        return None


    def process_file_content(self, content: list, chunk_size: int = 100, overlap_size: int = 20):
        
        # Create text splitter call object
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            length_function=len
        )

        # Document loader from Langchain has a response model for loaded docs
        # It return list of Document object and each obj has two attributes:
        #
        # 1) page_content: actual text extracted from document page
        # 2) metadat: other info about the doc (file_name, size, pages)
        # 
        # We will extract the page content for all the documnets and store it
        # in a list for later splitting  

        # Define empty list to hold all the extracted text
        texts = [ item.page_content for item in content ]

        print("=" * 50)
        print(" Text Loaded Success! ", texts[:5] )
        print("=" * 50)

        # Define empty list to hold all the metadata
        metadatas = [ item.metadata for item in content ]

        # Chunk the full text
        chunks = text_splitter.create_documents(texts, metadatas)

        return chunks


    async def process_file(self, request: ProcessRequest):

        file_id = request.file_id

        loader = self.get_file_loader(file_id=file_id)

        content = loader.load()

        chunks = self.process_file_content(content=content, chunk_size=request.chunk_size, overlap_size=request.overlap_size)

        # Convert Document objects to dicts
        json_chunks = self.to_json(chunks, file_id)

        return ProcessResponse.model_validate(json_chunks)



        

    