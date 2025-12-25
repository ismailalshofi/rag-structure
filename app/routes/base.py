from fastapi import FastAPI, APIRouter
import os

base_router = APIRouter(prefix='', tags=["Base"])

@base_router.get('/')
def health():

    app_name = os.getenv('APP_NAME')
    app_version = os.getenv('APP_VERSION')
    
    return {
        "message": "Welcome!",
        "appName": app_name,
        "appVersion": app_version
    }