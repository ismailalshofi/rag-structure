import logging
import os
import random
import re
import string

import aiofiles
from fastapi import UploadFile, status
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models import FileType, ResponseMessage
from app.services.project import ProjectService

logger = logging.getLogger("uvicorn.error")

SUPPORTED_EXTENSIONS = {t.value for t in FileType}


class UploadService:
    @staticmethod
    def validate(file: UploadFile) -> tuple[bool, str]:
        settings = get_settings()

        # Browsers and HTTP clients disagree on content types (.md is often octet-stream),
        # so the extension is what decides whether we can parse the file
        extension = os.path.splitext(file.filename or "")[-1].lower()
        if extension not in SUPPORTED_EXTENSIONS:
            return False, ResponseMessage.FILE_TYPE_NOT_SUPPORTED.value

        if file.size is not None and file.size > settings.FILE_MAX_SIZE:
            return False, ResponseMessage.FILE_SIZE_EXCEEDED.value

        return True, ResponseMessage.FILE_UPLOAD_SUCCESS.value

    @staticmethod
    def clean_file_name(file_name: str) -> str:
        return re.sub(r"[^\w.]", "", file_name.strip().replace(" ", "_"))

    @staticmethod
    def generate_random_string(length: int = 12) -> str:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    @staticmethod
    def generate_unique_file_path(file_name: str, project_id: str) -> tuple[str, str]:
        project_path = ProjectService.get_project_path(project_id)
        clean_name = UploadService.clean_file_name(file_name)

        while True:
            file_id = UploadService.generate_random_string() + "_" + clean_name
            file_path = os.path.join(project_path, file_id)
            if not os.path.exists(file_path):
                return file_path, file_id

    @staticmethod
    async def upload(project_id: str, file: UploadFile) -> JSONResponse:
        settings = get_settings()

        is_valid, message = UploadService.validate(file)
        if not is_valid:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": message})

        file_path, file_id = UploadService.generate_unique_file_path(file.filename, project_id)

        written = 0
        try:
            async with aiofiles.open(file_path, "wb") as f:
                while chunk := await file.read(settings.FILE_CHUNK_SIZE):
                    written += len(chunk)
                    # file.size isn't always sent, so check the size while writing too
                    if written > settings.FILE_MAX_SIZE:
                        raise ValueError(ResponseMessage.FILE_SIZE_EXCEEDED.value)
                    await f.write(chunk)
        except Exception as e:
            logger.error(f"Error while uploading file: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            too_big = str(e) == ResponseMessage.FILE_SIZE_EXCEEDED.value
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"message": str(e) if too_big else ResponseMessage.FILE_UPLOAD_FAILED.value},
            )

        return JSONResponse(content={"message": message, "file_id": file_id})
