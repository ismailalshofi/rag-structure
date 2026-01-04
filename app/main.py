from fastapi import FastAPI
from app.routes import base, file


app = FastAPI()
app.include_router(base.base_router)
app.include_router(file.file_router)