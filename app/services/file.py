
import os
from fastapi import UploadFile, status
from fastapi.responses import JSONResponse
from app.models import ResponseSignal
from app.services.project import ProjectService
from app.services.base import BaseService
import aiofiles 
import re
import logging

logger = logging.getLogger('uvicorn.error')


class FileService(BaseService):

    def __init__(self):
        super().__init__()

    def validate_file(self, file: UploadFile):

        if file.content_type not in self.app_settings.FILE_ALLOWED_EXTENSTIONS:
            return False, ResponseSignal.FILE_TYPE_NOT_SUPPORTED.value

        if file.size > self.app_settings.FILE_MAX_SIZE:
            return False, ResponseSignal.FILE_SIZE_EXCEEDED.value
        
        return True, ResponseSignal.FILE_UPLOAD_SUCCESS.value

    
    def generate_unique_file_path(self, origin_file_name: str, project_id: str):
        # Generate random str for file name 
        random_key = self.generate_random_string()
        project_path = ProjectService().get_project_path(project_id=project_id)

        # Get clean file name
        clean_file_name = self.get_clean_file_name(origin_file_name)

        new_file_path = os.path.join(project_path, random_key + "_" + clean_file_name)
        
        # Generate new random key if it exists
        while os.path.exists(new_file_path):
            random_key = self.generate_random_string()
            new_file_path = os.path.join(project_path, random_key + "_" + clean_file_name)

        return new_file_path, random_key


    def get_clean_file_name(self, file_name: str):
        
        # remove any special characters
        cleaned_file_name = re.sub(r'[^\w.]', '', file_name.strip())

        # replace space with underscore
        cleaned_file_name = cleaned_file_name.replace(" ", "_")

        return cleaned_file_name



    async def process_file(self, id: str, file: UploadFile):

        is_valid, message = self.validate_file(file=file)
        
        if not is_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message": message,
                },
            )
        
        # Get project dir to store the file inside it
        project_dir = ProjectService().get_project_path(project_id=id)

        # Generate new file name with a random string prefix  
        new_file_name, file_id = self.generate_unique_file_path(origin_file_name=file.filename, project_id=id)

        file_path = os.path.join(project_dir, new_file_name)

        try:
            # Write the file to assets/{project_id}
            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await file.read(size=self.app_settings.FILE_CHUNK_SIZE):
                    await f.write(chunk)

        except Exception as e:
            logger.error(f"Error while uploading file: {e}")
            return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": ResponseSignal.FILE_UPLOAD_FAILED,
            }
        )

        return JSONResponse(
            content={
                "message": message,
                "file_id": file_id
            }
        )


        