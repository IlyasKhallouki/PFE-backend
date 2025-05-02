from fastapi import APIRouter, Depends, HTTPException, status, Query
from models.message import Message
from schemas.message import MessageCreate, MessageRead
from core.dependencies import get_current_user

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def post_message(data: MessageCreate, user=Depends(get_current_user)):
    return await Message.create(author_id=user.id, **data.dict())  # relate author via FK :contentReference[oaicite:8]{index=8}

@router.get("", response_model=list[MessageRead])
async def list_messages(
    channel_id: int = Query(...), 
    limit: int = Query(50, ge=1, le=200),
    user=Depends(get_current_user)
):
    return await Message.filter(channel_id=channel_id).order_by("-sent_at").limit(limit)  # pagination basics :contentReference[oaicite:9]{index=9}

@router.get("/{id}", response_model=MessageRead)
async def get_message(id: int, user=Depends(get_current_user)):
    msg = await Message.get_or_none(id=id)
    if not msg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")
    return msg
