from fastapi import APIRouter, Depends

from app.config import get_settings, Settings

health_router = APIRouter(prefix='', tags=["Health"])


@health_router.get('/')
def health(settings: Settings = Depends(get_settings)):
    app_name = settings.APP_NAME
    app_version = settings.APP_VERSION

    return {
        "message": "Welcome!",
        "appName": app_name,
        "appVersion": app_version
    }
