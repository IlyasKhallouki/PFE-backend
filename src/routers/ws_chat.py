# routers/ws_chat.py
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, status, Depends
from tortoise.exceptions import DoesNotExist
from datetime import datetime
import json
from typing import Dict, List, Set
import asyncio
import httpx

from core.dependencies import get_current_user_ws
from models import channel as ch_model, message as msg_model, user as user_model
from models.channelmember import ChannelMember

router = APIRouter()

AI_SERVICE_URL = "http://127.0.0.1:8001"

# --- No changes in ConnectionManager class ---
class ConnectionManager:
    """Enhanced WebSocket connection manager with presence tracking"""
    
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.user_channels: Dict[int, Set[int]] = {}
        self.channel_users: Dict[int, Set[int]] = {}
        self.websocket_users: Dict[WebSocket, int] = {}
        
    async def connect(self, channel_id: int, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = []
        self.active_connections[channel_id].append(websocket)
        self.websocket_users[websocket] = user_id
        if user_id not in self.user_channels:
            self.user_channels[user_id] = set()
        self.user_channels[user_id].add(channel_id)
        if channel_id not in self.channel_users:
            self.channel_users[channel_id] = set()
        self.channel_users[channel_id].add(user_id)
        
    def disconnect(self, channel_id: int, user_id: int, websocket: WebSocket):
        if channel_id in self.active_connections:
            if websocket in self.active_connections[channel_id]:
                self.active_connections[channel_id].remove(websocket)
            if not self.active_connections[channel_id]:
                del self.active_connections[channel_id]
        if websocket in self.websocket_users:
            del self.websocket_users[websocket]
        if user_id in self.user_channels:
            self.user_channels[user_id].discard(channel_id)
            if not self.user_channels[user_id]:
                del self.user_channels[user_id]
        if channel_id in self.channel_users:
            self.channel_users[channel_id].discard(user_id)
            if not self.channel_users[channel_id]:
                del self.channel_users[channel_id]
                
    async def broadcast(self, channel_id: int, message: dict, exclude_ws: WebSocket = None):
        if channel_id not in self.active_connections:
            return
        disconnected = []
        for websocket in self.active_connections[channel_id]:
            if websocket != exclude_ws:
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.append(websocket)
        for ws in disconnected:
            if ws in self.websocket_users:
                user_id = self.websocket_users[ws]
                self.disconnect(channel_id, user_id, ws)

manager = ConnectionManager()

# --- MODIFICATION START: Corrected function signature ---
@router.websocket("/ws/{channel_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel_id: int,
):
# --- MODIFICATION END ---
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        user = await get_current_user_ws(token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        channel = await ch_model.Channel.get(id=channel_id)
    except DoesNotExist:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        return
        
    # --- Check for Chatbot Channel ---
    is_chatbot_channel = False
    # --- MODIFICATION START: Access state via websocket.app ---
    chatbot_user_id = websocket.app.state.chatbot_user_id
    # --- MODIFICATION END ---
    if channel.is_private:
        members = await ChannelMember.filter(channel_id=channel_id).values_list("user_id", flat=True)
        if set(members) == {user.id, chatbot_user_id}:
            is_chatbot_channel = True
    # --- End Check ---

    if channel.is_private and not is_chatbot_channel:
        is_member = await ChannelMember.filter(channel_id=channel_id, user_id=user.id).exists()
        if not is_member:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    elif not channel.is_private and channel.role_id and channel.role_id != user.role_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(channel_id, user.id, websocket)
    
    try:
        messages = await msg_model.Message.filter(channel_id=channel_id).order_by("-sent_at").limit(50).prefetch_related("author")
        history = [{"id": msg.id, "author": msg.author.full_name, "author_id": msg.author.id, "content": msg.content, "sent_at": msg.sent_at.isoformat()} for msg in reversed(messages)]
        await websocket.send_json({"type": "history", "data": history})
        active_user_ids = list(manager.channel_users.get(channel_id, set()))
        await websocket.send_json({"type": "active_users", "data": active_user_ids})
        await manager.broadcast(
            channel_id,
            {"type": "user_joined", "data": {"user_id": user.id, "user_name": user.full_name}},
            exclude_ws=websocket
        )
        
        while True:
            text = (await websocket.receive_text()).strip()

            if is_chatbot_channel:
                history_messages = await msg_model.Message.filter(channel_id=channel_id).order_by("sent_at").limit(10)
                past_user_inputs = [m.content for m in history_messages if m.author_id == user.id]
                generated_responses = [m.content for m in history_messages if m.author_id == chatbot_user_id]
                
                bot_reply_content = "Sorry, something went wrong."
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(
                            f"{AI_SERVICE_URL}/api/v1/chat",
                            json={
                                "text": text,
                                "past_user_inputs": past_user_inputs,
                                "generated_responses": generated_responses
                            },
                            timeout=30.0
                        )
                        if response.status_code == 200:
                            bot_reply_content = response.json().get("reply", bot_reply_content)
                except httpx.RequestError:
                    bot_reply_content = "I am having trouble connecting to my brain right now."
                
                await msg_model.Message.create(content=text, channel_id=channel_id, author_id=user.id)
                bot_message = await msg_model.Message.create(content=bot_reply_content, channel_id=channel_id, author_id=chatbot_user_id)
                
                await websocket.send_json({
                    "type": "message",
                    "data": {
                        "id": bot_message.id,
                        "author": "Chatbot",
                        "author_id": chatbot_user_id,
                        "content": bot_message.content,
                        "sent_at": bot_message.sent_at.isoformat()
                    }
                })
                continue

            if text.lower().startswith("/summarize"):
                recent_messages = await msg_model.Message.filter(channel_id=channel_id).order_by("-sent_at").limit(50).prefetch_related("author")
                if not recent_messages:
                    await websocket.send_json({"type": "system_message", "data": {"content": "Not enough messages to summarize."}})
                    continue
                chat_text = "\n".join([f"{msg.author.full_name}: {msg.content}" for msg in reversed(recent_messages)])
                summary = "Could not generate a summary."
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.post(f"{AI_SERVICE_URL}/api/v1/summarize", json={"text": chat_text}, timeout=30.0)
                        if response.status_code == 200:
                            summary = response.json().get("summary", summary)
                        else:
                            summary = f"Error: Could not contact AI service (status: {response.status_code})."
                except httpx.RequestError as e:
                    summary = f"Error: Could not connect to AI service: {e}"
                await manager.broadcast(channel_id, {"type": "message", "data": {"id": 0, "author": "Summary Bot", "author_id": 0, "content": summary, "sent_at": datetime.utcnow().isoformat()}})
                continue

            message = await msg_model.Message.create(content=text, channel_id=channel_id, author_id=user.id)
            await manager.broadcast(channel_id, {"type": "message", "data": {"id": message.id, "author": user.full_name, "author_id": user.id, "content": message.content, "sent_at": message.sent_at.isoformat()}})
                
    except WebSocketDisconnect:
        manager.disconnect(channel_id, user.id, websocket)
        await manager.broadcast(channel_id, {"type": "user_left", "data": {"user_id": user.id, "user_name": user.full_name}})