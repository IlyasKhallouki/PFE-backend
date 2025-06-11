# routers/ws_chat.py
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, status, Depends, Query
from tortoise.exceptions import DoesNotExist
from datetime import datetime
import json
from typing import Dict, List, Set
import asyncio

from core.dependencies import get_current_user_ws
from models import channel as ch_model, message as msg_model, user as user_model
from models.channelmember import ChannelMember

router = APIRouter()

class ConnectionManager:
    """Enhanced WebSocket connection manager with presence tracking"""
    
    def __init__(self):
        # Channel ID -> List of WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
        # User ID -> Set of channel IDs they're active in
        self.user_channels: Dict[int, Set[int]] = {}
        # Channel ID -> Set of active user IDs
        self.channel_users: Dict[int, Set[int]] = {}
        # WebSocket -> User ID mapping
        self.websocket_users: Dict[WebSocket, int] = {}
        
    async def connect(self, channel_id: int, user_id: int, websocket: WebSocket):
        """Connect a user to a channel"""
        await websocket.accept()
        
        # Add to connections
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = []
        self.active_connections[channel_id].append(websocket)
        
        # Map websocket to user
        self.websocket_users[websocket] = user_id
        
        # Track user presence
        if user_id not in self.user_channels:
            self.user_channels[user_id] = set()
        self.user_channels[user_id].add(channel_id)
        
        if channel_id not in self.channel_users:
            self.channel_users[channel_id] = set()
        self.channel_users[channel_id].add(user_id)
        
    def disconnect(self, channel_id: int, user_id: int, websocket: WebSocket):
        """Disconnect a user from a channel"""
        if channel_id in self.active_connections:
            if websocket in self.active_connections[channel_id]:
                self.active_connections[channel_id].remove(websocket)
            if not self.active_connections[channel_id]:
                del self.active_connections[channel_id]
                
        # Remove websocket mapping
        if websocket in self.websocket_users:
            del self.websocket_users[websocket]
                
        # Update presence tracking
        if user_id in self.user_channels:
            self.user_channels[user_id].discard(channel_id)
            if not self.user_channels[user_id]:
                del self.user_channels[user_id]
                
        if channel_id in self.channel_users:
            self.channel_users[channel_id].discard(user_id)
            if not self.channel_users[channel_id]:
                del self.channel_users[channel_id]
                
    async def broadcast(self, channel_id: int, message: dict, exclude_ws: WebSocket = None):
        """Broadcast a message to all connections in a channel"""
        if channel_id not in self.active_connections:
            return
            
        disconnected = []
        for websocket in self.active_connections[channel_id]:
            if websocket != exclude_ws:
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.append(websocket)
                    
        # Clean up disconnected sockets
        for ws in disconnected:
            if ws in self.websocket_users:
                user_id = self.websocket_users[ws]
                self.disconnect(channel_id, user_id, ws)

manager = ConnectionManager()

@router.websocket("/ws/{channel_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel_id: int,
):
    """Enhanced WebSocket endpoint with better error handling"""
    
    # Get token from query params or cookies
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Authenticate user
    try:
        user = await get_current_user_ws(token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    # Verify channel access
    try:
        channel = await ch_model.Channel.get(id=channel_id).prefetch_related("role")
    except DoesNotExist:
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA)
        return
        
    # Check permissions
    if channel.is_private:
        is_member = await ChannelMember.filter(
            channel_id=channel_id, 
            user_id=user.id
        ).exists()
        if not is_member:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    elif channel.role_id and channel.role_id != user.role_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    # Connect user
    await manager.connect(channel_id, user.id, websocket)
    
    try:
        # Send message history
        messages = await msg_model.Message.filter(
            channel_id=channel_id
        ).order_by("-sent_at").limit(50).prefetch_related("author")
        
        history = [
            {
                "id": msg.id,
                "author": msg.author.full_name,
                "author_id": msg.author.id,
                "content": msg.content,
                "sent_at": msg.sent_at.isoformat()
            }
            for msg in reversed(messages)
        ]
        
        await websocket.send_json({
            "type": "history",
            "data": history
        })
        
        # Send active users
        active_user_ids = list(manager.channel_users.get(channel_id, set()))
        await websocket.send_json({
            "type": "active_users",
            "data": active_user_ids
        })
        
        # Broadcast user joined
        await manager.broadcast(
            channel_id,
            {
                "type": "user_joined",
                "data": {
                    "user_id": user.id,
                    "user_name": user.full_name
                }
            },
            exclude_ws=websocket
        )
        
        # Handle incoming messages
        while True:
            text = await websocket.receive_text()
            
            # Create message in database
            message = await msg_model.Message.create(
                content=text.strip(),
                channel_id=channel_id,
                author_id=user.id
            )
            
            # Broadcast to all users
            await manager.broadcast(
                channel_id,
                {
                    "type": "message",
                    "data": {
                        "id": message.id,
                        "author": user.full_name,
                        "author_id": user.id,
                        "content": message.content,
                        "sent_at": message.sent_at.isoformat()
                    }
                }
            )
                
    except WebSocketDisconnect:
        manager.disconnect(channel_id, user.id, websocket)
        
        # Broadcast user left
        await manager.broadcast(
            channel_id,
            {
                "type": "user_left",
                "data": {
                    "user_id": user.id,
                    "user_name": user.full_name
                }
            }
        )