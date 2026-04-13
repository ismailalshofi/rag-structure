import os


class ProjectService:

    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    FILES_DIR = os.path.join(BASE_DIR, "assets/files")

    @staticmethod
    def get_project_path(project_id: str) -> str:
        project_dir = os.path.join(ProjectService.FILES_DIR, project_id)

        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        return project_dir
