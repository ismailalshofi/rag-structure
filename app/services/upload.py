import os
import re
import random
import string
import logging

import aiofiles
from fastapi import UploadFile, status
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models import ResponseMessage
from app.services.project import ProjectService

logger = logging.getLogger('uvicorn.error')


class UploadService:

    @staticmethod
    def validate(file: UploadFile):
        settings = get_settings()

        if file.content_type not in settings.FILE_ALLOWED_EXTENSIONS:
            return False, ResponseMessage.FILE_TYPE_NOT_SUPPORTED.value

        if file.size > settings.FILE_MAX_SIZE:
            return False, ResponseMessage.FILE_SIZE_EXCEEDED.value

        return True, ResponseMessage.FILE_UPLOAD_SUCCESS.value

    @staticmethod
    def clean_file_name(file_name: str) -> str:
        cleaned = re.sub(r'[^\w.]', '', file_name.strip())
        cleaned = cleaned.replace(" ", "_")
        return cleaned

    @staticmethod
    def generate_random_string(length: int = 12) -> str:
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    @staticmethod
    def generate_unique_file_path(file_name: str, project_id: str) -> tuple[str, str]:
        random_key = UploadService.generate_random_string()
        project_path = ProjectService.get_project_path(project_id)
        clean_name = UploadService.clean_file_name(file_name)

        file_id = random_key + "_" + clean_name
        file_path = os.path.join(project_path, file_id)

        while os.path.exists(file_path):
            random_key = UploadService.generate_random_string()
            file_id = random_key + "_" + clean_name
            file_path = os.path.join(project_path, file_id)

        return file_path, file_id

    @staticmethod
    async def upload(project_id: str, file: UploadFile):
        settings = get_settings()

        is_valid, message = UploadService.validate(file)

        if not is_valid:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": message},
            )

        file_path, file_id = UploadService.generate_unique_file_path(file.filename, project_id)

        try:
            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await file.read(size=settings.FILE_CHUNK_SIZE):
                    await f.write(chunk)

        except Exception as e:
            logger.error(f"Error while uploading file: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": ResponseMessage.FILE_UPLOAD_FAILED.value},
            )

        return JSONResponse(
            content={"message": message, "file_id": file_id}
        )
