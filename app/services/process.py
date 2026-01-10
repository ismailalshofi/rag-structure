from mimetypes import init
import os
from app.services.base import BaseService
from app.services.project import ProjectService


class ProcessService(BaseService):

    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.project_path = ProjectService().get_project_path(project_id=project_id)

    def get_file_extenstion(self, file_id):
        return os.path.splitext(file_id)[-1]

    