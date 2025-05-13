from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from core.config import settings

TORTOISE_ORM = {
    "connections": {
        "default": settings.DATABASE_URL
    },
    "apps": {
        "models": {
            "models": [
                "models.user",
                "models.channel",
                "models.channelmember",
                "models.message",
                "models.role",
                "aerich.models"               
            ],
            "default_connection": "default",
        },
    },
}

def init_db(app):
    """
    Initialize Tortoise ORM with FastAPI.
    Auto-creates tables on first run if generate_schemas=True.
    """
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    )
