from fastapi import APIRouter, Depends, HTTPException, status
from models.channel import Channel               # your Tortoise model
from schemas.channel import ChannelCreate, ChannelRead
from core.dependencies import get_current_user

router = APIRouter(prefix="/channels", tags=["channels"])

@router.post("", response_model=ChannelRead, status_code=status.HTTP_201_CREATED)
async def create_channel(data: ChannelCreate, user=Depends(get_current_user)):
    return await Channel.create(**data.dict())

@router.get("", response_model=list[ChannelRead])
async def list_channels(user=Depends(get_current_user)):
    return await Channel.all().order_by("name")

@router.get("/{id}", response_model=ChannelRead)
async def get_channel(id: int, user=Depends(get_current_user)):
    channel = await Channel.get_or_none(id=id)      
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel

@router.put("/{id}", response_model=ChannelRead)
async def update_channel(id: int, data: ChannelCreate, user=Depends(get_current_user)):
    channel = await Channel.get_or_none(id=id)
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    await channel.update_from_dict(data.dict()).save()
    return await Channel.get(id=id)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(id: int, user=Depends(get_current_user)):
    deleted_count = await Channel.filter(id=id).delete()
    if not deleted_count:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return None
