from fastapi import FastAPI
from core.database import init_db
from routers.auth import router as auth_router
from routers.channels import router as channel_router
from routers.messages import router as message_router
from routers.ws_chat import router as ws_chat_router
from core.config import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db(app)                   
app.include_router(channel_router)
app.include_router(message_router)
app.include_router(auth_router)  
app.include_router(ws_chat_router)