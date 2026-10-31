import os
import re

PROJECT_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class ProjectService:
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    FILES_DIR = os.path.join(BASE_DIR, "assets/files")

    @staticmethod
    def is_valid_id(project_id: str) -> bool:
        # Project ids become folder and table names, so no slashes, dots or spaces
        return bool(PROJECT_ID.match(project_id))

    @staticmethod
    def get_project_path(project_id: str) -> str:
        project_dir = os.path.join(ProjectService.FILES_DIR, project_id)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir

    @staticmethod
    def get_file_path(project_id: str, file_id: str) -> str | None:
        # file_id must be a plain file name inside the project folder
        if os.path.basename(file_id) != file_id:
            return None
        path = os.path.join(ProjectService.get_project_path(project_id), file_id)
        return path if os.path.isfile(path) else None

    @staticmethod
    def collection_name(project_id: str) -> str:
        return f"project_{project_id}"
