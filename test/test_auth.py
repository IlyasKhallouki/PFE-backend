import pytest
from src.core.security import get_password_hash
from src.models.user import User

@pytest.mark.anyio
async def test_login_success(client):
    # Prepare a user
    pw = "secret123"
    hashed = get_password_hash(pw)
    await User.create(email="test@example.com", hashed_pw=hashed, role="member")
    # Attempt login
    response = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": pw},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    # Cookie should be set
    assert "access_token" in response.cookies

@pytest.mark.anyio
async def test_login_failure(client):
    # No user in DB
    response = await client.post(
        "/auth/login",
        json={"email": "doesnotexist@example.com", "password": "bad"},
    )
    assert response.status_code == 401
