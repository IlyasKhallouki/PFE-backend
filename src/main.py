from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.exceptions import DoesNotExist

from routers import auth, channels, messages, ws_chat, roles, users, dm
from core.database import init_db
from core.security import hash_password # <--- Add this import
from models.user import User # <--- Add this import
from models.role import Role # <--- Add this import

app = FastAPI()

# --- ADD STARTUP EVENT ---
@app.on_event("startup")
async def startup_event():
    """
    Creates a dedicated "Chatbot" user and a default "member" role on startup 
    if they don't already exist.
    """
    print("Running startup event...")
    # Ensure a "member" role exists, as the bot will need it.
    member_role, _ = await Role.get_or_create(
        name="member",
        defaults={"description": "Regular user role"}
    )
    
    # Create the chatbot user if it doesn't exist
    chatbot_user, created = await User.get_or_create(
        email="chatbot@internal.local",
        defaults={
            "full_name": "Chatbot",
            "hashed_password": hash_password("you-cannot-login-as-the-bot"),
            "role": member_role,
        }
    )
    if created:
        print("Chatbot user created.")
    
    # Store the chatbot's ID in the app's state for easy access
    app.state.chatbot_user_id = chatbot_user.id
    print(f"Chatbot user ID ({app.state.chatbot_user_id}) is available in app.state")
# --- END STARTUP EVENT ---


origins = ["http://localhost:3000", "http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(auth.router, prefix="/auth")
app.include_router(channels.router)
app.include_router(messages.router)
app.include_router(ws_chat.router)
app.include_router(roles.router)
app.include_router(users.router)
app.include_router(dm.router)

init_db(app)