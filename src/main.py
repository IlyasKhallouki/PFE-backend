from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth, channels, messages, ws_chat, roles, users, dm
from core.database import init_db

app = FastAPI()

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(channels.router)
app.include_router(messages.router)
app.include_router(ws_chat.router)
app.include_router(roles.router)
app.include_router(users.router)
app.include_router(dm.router)

init_db(app)