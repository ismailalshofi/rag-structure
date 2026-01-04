
import os
from app.helpers.config import get_settings, Settings

class BaseService:

    app_settings = Settings

    def __init__(self):
        self.app_settings = get_settings()
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.file_dir = os.path.join(self.base_dir, "assets/files")