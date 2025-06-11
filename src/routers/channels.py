from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from models.channel import Channel
from models.channelmember import ChannelMember
from models.user import User
from core.dependencies import get_current_user
from pydantic import BaseModel

from tortoise.expressions import Q

router = APIRouter(prefix="/channels", tags=["channels"])


class ChannelCreate(BaseModel):
    name: str
    is_private: bool = False
    role_id: int | None = None
    members: List[int] | None = None  # only when private


@router.get("/", dependencies=[Depends(get_current_user)])
async def list_my_channels(user: User = Depends(get_current_user)):
    # Get public channels and private channels the user is a member of
    public_channels = await Channel.filter(
        is_private=False,
        role_id__in=[None, user.role_id] if user.role_id else [None]
    ).all()
    
    # Get private channels through membership
    private_channel_ids = await ChannelMember.filter(
        user_id=user.id
    ).values_list("channel_id", flat=True)
    
    private_channels = await Channel.filter(
        id__in=private_channel_ids,
        is_private=True
    ).all()
    
    # Combine and format
    all_channels = public_channels + private_channels
    
    return [
        {
            "id": ch.id,
            "name": ch.name,
            "is_private": ch.is_private
        }
        for ch in all_channels
    ]


@router.post("/", status_code=201)
async def create_channel(payload: ChannelCreate, user: User = Depends(get_current_user)):
    # if role‑bound, only admins can create
    if payload.role_id and (user.role is None or user.role.name != "admin"):
        raise HTTPException(status_code=403)

    ch = await Channel.create(name=payload.name, is_private=payload.is_private, role_id=payload.role_id)
    if payload.is_private and payload.members:
        for uid in payload.members + [user.id]:
            await ChannelMember.get_or_create(channel_id=ch.id, user_id=uid)
    return {"id": ch.id, "name": ch.name, "is_private": ch.is_private}