from fastapi import WebSocket, WebSocketDisconnect, APIRouter, status, Depends
from tortoise.exceptions import DoesNotExist

from core.dependencies import get_current_user
from models import channel as ch_model, message as msg_model
from .channels import ChannelMember  # ensure import for membership check

router = APIRouter()

class Manager:  # keeps per‑channel connections
    def __init__(self):
        self.active = {}

    async def connect(self, cid: int, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(cid, []).append(ws)

    def disconnect(self, cid: int, ws: WebSocket):
        if cid in self.active and ws in self.active[cid]:
            self.active[cid].remove(ws)
            if not self.active[cid]:
                del self.active[cid]

    async def broadcast(self, cid: int, data: dict):
        for ws in self.active.get(cid, []):
            await ws.send_json(data)

manager = Manager()


@router.websocket("/ws/{channel_id}")
async def chat_ws(ws: WebSocket, channel_id: int, user=Depends(get_current_user)):
    try:
        channel = await ch_model.Channel.get(id=channel_id).prefetch_related("role")
    except DoesNotExist:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # access control
    if channel.is_private:
        if not await ChannelMember.filter(channel_id=channel_id, user_id=user.id).exists():
            await ws.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    elif channel.role_id and channel.role_id != user.role_id:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(channel_id, ws)

    # history (last 50)
    hist = (
        await msg_model.Message.filter(channel_id=channel_id).order_by("-sent_at").limit(50).prefetch_related("author")
    )[::-1]
    await ws.send_json({
        "type": "history",
        "data": [
            {"id": m.id, "author": m.author.email, "content": m.content, "sent_at": m.sent_at.isoformat()} for m in hist
        ],
    })

    try:
        while True:
            text = await ws.receive_text()
            m = await msg_model.Message.create(content=text, channel_id=channel_id, author_id=user.id)
            payload = {"type": "message", "data": {"id": m.id, "author": user.full_name, "content": text, "sent_at": m.sent_at.isoformat()}}
            await manager.broadcast(channel_id, payload)
    except WebSocketDisconnect:
        manager.disconnect(channel_id, ws)