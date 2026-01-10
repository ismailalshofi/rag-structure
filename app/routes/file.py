
from fastapi import APIRouter, UploadFile
from app.services import FileService, file
from app.schema import ProcessRequest
from app.services import ProcessService

file_router = APIRouter(prefix='/api/file', tags=["File"])

@file_router.post('/upload/{project_id}')
async def upload_file(
    project_id: str,
    file: UploadFile,
    ):
    return await FileService().upload_file(id=project_id, file=file)


@file_router.post('/process/{project_id}')
async def process_file(
    project_id: str,
    process_request: ProcessRequest
    ):
    return await ProcessService().process_file(request=process_request)
