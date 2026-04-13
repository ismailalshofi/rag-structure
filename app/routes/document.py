from fastapi import APIRouter, UploadFile

from app.schemas import ProcessRequest
from app.services import UploadService, ProcessingService

document_router = APIRouter(prefix='/api/document', tags=["Document"])


@document_router.post('/upload/{project_id}')
async def upload_file(project_id: str, file: UploadFile):
    return await UploadService.upload(project_id, file)


@document_router.post('/process/{project_id}')
async def process_file(project_id: str, request: ProcessRequest):
    return await ProcessingService.process(project_id, request)
