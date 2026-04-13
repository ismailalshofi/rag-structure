from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    FILE_ALLOWED_EXTENSIONS: list[str]
    FILE_MAX_SIZE: int
    FILE_CHUNK_SIZE: int

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()
