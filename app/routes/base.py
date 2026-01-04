from fastapi import APIRouter, Depends

from app.helpers.config import get_settings, Settings

base_router = APIRouter(prefix='', tags=["Base"])

@base_router.get('/')
def health(settings: Settings = Depends(get_settings)):

    app_name = settings.APP_NAME
    app_version = settings.APP_VERSION
    
    return {
        "message": "Welcome!",
        "appName": app_name,
        "appVersion": app_version
    }