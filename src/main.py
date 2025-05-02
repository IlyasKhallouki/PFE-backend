from fastapi import FastAPI
from core.database import init_db
from routers.auth import router as auth_router
from routers.channels import router as channel_router
from routers.messages import router as message_router
from core.config import settings


app = FastAPI()
init_db(app)                   
app.include_router(channel_router)
app.include_router(message_router)
app.include_router(auth_router)  
