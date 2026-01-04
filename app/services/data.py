
import os
from fastapi import UploadFile, status
from fastapi.responses import JSONResponse
from app.models import ResponseSignal
from app.services.project import ProjectService
from app.services.base import BaseService
import aiofiles 


class DataService(BaseService):

    def __init__(self):
        super().__init__()

    def validate_file(self, file: UploadFile):

        if file.content_type not in self.app_settings.FILE_ALLOWED_EXTENSTIONS:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if file.size > self.app_settings.FILE_MAX_SIZE:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value
        
        return True, ResponseSignal.FILE_UPLOAD_SUCCESS.value


    async def process_file(self, id: str, file: UploadFile):

        is_valid, message = self.validate_file(file=file)
        
        if not is_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": message,
                },
            )
        
        project_dir = ProjectService().get_project_path(project_id=id)
        file_path = os.path.join(project_dir, file.filename)

        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(size=self.app_settings.FILE_CHUNK_SIZE):
                await f.write(chunk)


        