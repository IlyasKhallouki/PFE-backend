from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from typing import Dict, List
from tortoise.exceptions import DoesNotExist

from core.security import decode_access_token
from models import message as msg_model, user as user_model

router = APIRouter()

# ————————————————————————————————
# in‑memory connection registry (per‑channel)
# ————————————————————————————————

class ConnectionManager:
    def __init__(self):
        self.active: Dict[int, List[WebSocket]] = {}

    async def connect(self, ch_id: int, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(ch_id, []).append(ws)

    def disconnect(self, ch_id: int, ws: WebSocket):
        self.active.get(ch_id, []).remove(ws)
        if not self.active[ch_id]:
            del self.active[ch_id]

    async def broadcast(self, ch_id: int, payload: dict):
        for ws in self.active.get(ch_id, []):
            await ws.send_json(payload)

manager = ConnectionManager()

# ————————————————————————————————
# WebSocket endpoint
# ————————————————————————————————

@router.websocket("/ws/{channel_id}")
async def chat_ws(ws: WebSocket, channel_id: int):
    token = ws.cookies.get("access_token")
    payload = decode_access_token(token) if token else None
    if not payload:
        # unauthenticated – close with policy violation
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        user = await user_model.User.get(email=payload.get("sub"))
    except DoesNotExist:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(channel_id, ws)

    # Send conversation history (latest 50)
    history = (
        await msg_model.Message.filter(channel_id=channel_id)
        .order_by("-sent_at")
        .limit(50)
        .prefetch_related("author")
    )
    await ws.send_json({
        "type": "history",
        "data": [
            {
                "id": m.id,
                "author": m.author.email,
                "content": m.content,
                "sent_at": m.sent_at.isoformat(),
            }
            for m in reversed(history)
        ],
    })

    try:
        while True:
            content = await ws.receive_text()
            # persist message
            msg_obj = await msg_model.Message.create(
                content=content, channel_id=channel_id, author_id=user.id
            )
            out = {
                "type": "message",
                "data": {
                    "id": msg_obj.id,
                    "author": user.email,
                    "content": content,
                    "sent_at": msg_obj.sent_at.isoformat(),
                },
            }
            await manager.broadcast(channel_id, out)
    except WebSocketDisconnect:
        manager.disconnect(channel_id, ws)