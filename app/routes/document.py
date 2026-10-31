from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.dependencies import RAG, get_rag, valid_project
from app.models import ResponseMessage
from app.schemas import IndexRequest, IndexResponse
from app.services import ProjectService, UploadService

document_router = APIRouter(prefix="/api/document", tags=["Document"])


@document_router.post("/upload/{project_id}")
async def upload_file(file: UploadFile, project_id: str = Depends(valid_project)):
    return await UploadService.upload(project_id, file)


@document_router.post("/index/{project_id}", response_model=IndexResponse)
def index_file(request: IndexRequest, project_id: str = Depends(valid_project), rag: RAG = Depends(get_rag)):
    file_path = ProjectService.get_file_path(project_id, request.file_id)
    if not file_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, ResponseMessage.FILE_NOT_FOUND.value)

    chunk_size = request.chunk_size or rag.settings.CHUNK_SIZE
    overlap = request.overlap if request.overlap is not None else rag.settings.CHUNK_OVERLAP
    total = rag.indexing.index_file(project_id, file_path, request.file_id, chunk_size, min(overlap, chunk_size - 1))
    return IndexResponse(message=ResponseMessage.INDEXING_SUCCESS.value, file_id=request.file_id, total_chunks=total)


@document_router.delete("/{project_id}/{file_id}")
def delete_file(file_id: str, project_id: str = Depends(valid_project), rag: RAG = Depends(get_rag)):
    rag.indexing.delete_file(project_id, file_id)
    return {"message": ResponseMessage.FILE_DELETED.value, "file_id": file_id}
