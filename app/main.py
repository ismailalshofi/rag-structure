from fastapi import FastAPI
from app.routes import health, document

app = FastAPI()

app.include_router(health.health_router)
app.include_router(document.document_router)
