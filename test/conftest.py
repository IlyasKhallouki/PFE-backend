# backend/src/tests/conftest.py

import sys, os, pytest
from fastapi import FastAPI
from httpx import AsyncClient
from httpx import ASGITransport
from tortoise.contrib.fastapi import register_tortoise
from src.core.config import settings

# 1) Ensure src/ is on the path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
SRC  = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from src.main import app  # now importable thanks to the sys.path tweak

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session", autouse=True)
async def init_db():
    # 2) Register Tortoise with in-memory SQLite for fast, ephemeral tests
    register_tortoise(
        app,
        db_url="sqlite://:memory:",
        modules={
            "models": [
                "src.models.user",
                "src.models.channel",
                "src.models.channelmember",
                "src.models.message",
                "aerich.models"
            ]
        },
        generate_schemas=True,
        add_exception_handlers=True,
    )
    yield
    # No teardown needed for in-memory DB

@pytest.fixture
async def client():
    """
    Provides an AsyncClient with ASGITransport so you can await requests
    without an actual HTTP server.
    """
    transport = ASGITransport(app=app)  # HTTPX transport into the ASGI app :contentReference[oaicite:4]{index=4}
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac  # anyio will run this fixture in an AsyncIO event loop :contentReference[oaicite:5]{index=5}
