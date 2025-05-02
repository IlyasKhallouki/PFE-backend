import pytest
from src.core.security import get_password_hash
from src.models.user import User
from src.models.channel import Channel

@pytest.mark.anyio
async def test_messages_crud(client):
    # --- Setup user & channel ---
    pw = "secret123"
    hashed = get_password_hash(pw)
    user = await User.create(email="msguser@example.com", hashed_pw=hashed, role="member")
    await client.post("/auth/login", json={"email":user.email,"password":pw})
    channel = await Channel.create(name="chat", is_private=False)

    # --- Post message ---
    resp = await client.post(
        "/messages",
        json={"channel_id": channel.id, "content": "Hello world"}
    )
    assert resp.status_code == 201
    msg = resp.json()
    assert msg["content"] == "Hello world"
    assert msg["channel_id"] == channel.id
    mid = msg["id"]

    # --- List messages ---
    resp = await client.get(f"/messages?channel_id={channel.id}&limit=10")
    assert resp.status_code == 200
    contents = [m["content"] for m in resp.json()]
    assert "Hello world" in contents

    # --- Retrieve single message ---
    resp = await client.get(f"/messages/{mid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == mid
