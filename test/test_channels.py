import pytest
from src.core.security import get_password_hash
from src.models.user import User

@pytest.mark.anyio
async def test_channels_crud(client):
    # --- Authenticate ---
    pw = "secret123"
    hashed = get_password_hash(pw)
    await User.create(email="user@example.com", hashed_pw=hashed, role="member")
    await client.post("/auth/login", json={"email":"user@example.com","password":pw})

    # --- Create ---
    resp = await client.post("/channels", json={"name":"general","is_private":False})
    assert resp.status_code == 201
    channel = resp.json()
    assert channel["name"] == "general"
    cid = channel["id"]

    # --- List ---
    resp = await client.get("/channels")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "general" in names

    # --- Retrieve ---
    resp = await client.get(f"/channels/{cid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == cid

    # --- Update ---
    resp = await client.put(
        f"/channels/{cid}",
        json={"name":"random","is_private":True}
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "random"
    assert resp.json()["is_private"] is True

    # --- Delete ---
    resp = await client.delete(f"/channels/{cid}")
    assert resp.status_code == 204

    # --- Not Found after delete ---
    resp = await client.get(f"/channels/{cid}")
    assert resp.status_code == 404
