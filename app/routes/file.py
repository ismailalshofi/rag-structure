
from fastapi import APIRouter, UploadFile
from app.services import FileService

file_router = APIRouter(prefix='/api/file', tags=["File"])

@file_router.post('/upload/{project_id}')
async def upload_file(
    project_id: str,
    file: UploadFile,
    ):
    return await FileService().process_file(id=project_id, file=file)
