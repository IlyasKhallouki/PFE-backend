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
    qs = Channel.filter(
        Q(is_private=False) | Q(members__user_id=user.id)
    )
    return [
        {"id": c.id, "name": c.name, "is_private": c.is_private}
        async for c in qs
        if c.role_id is None or c.role_id == user.role_id
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