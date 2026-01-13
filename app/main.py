from fastapi import FastAPI
from app.routes import base, file
from motor.motor_asyncio import AsyncIOMotorClient
from app.helpers.config import Settings, get_settings


app = FastAPI()
 
@app.on_event("startup")
async def startup():
    settings = get_settings()
    
    # Start MongoDB connection
    app.mongo_connection = AsyncIOMotorClient(settings.MONGODB_URL)
    app.db_client = app.mongo_connection[settings.MONGODB_DATABASE]

@app.on_event("shutdown")
async def shutdown():
    # Close MongoDB connection
    app.mongo_connection.close()



app.include_router(base.base_router)
app.include_router(file.file_router)