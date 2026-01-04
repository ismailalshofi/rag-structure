
from fastapi import APIRouter, UploadFile
from app.services import DataService

data_router = APIRouter(prefix='/api/data', tags=["Base"])

@data_router.post('/upload/{project_id}')
async def upload_data(
    project_id: str, 
    file: UploadFile,
    ):
    return await DataService().process_file(id=project_id, file=file)
