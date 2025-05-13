# routers/dm.py 
from fastapi import APIRouter, Depends, HTTPException, status
from tortoise.transactions import in_transaction
from tortoise.exceptions import IntegrityError
from models.user import User
from models.channel import Channel
from models.channelmember import ChannelMember
from core.dependencies import get_current_user

router = APIRouter(prefix="/dms", tags=["direct messages"])

@router.get("/recipients", response_model=list[int])
async def list_recipients(me: User = Depends(get_current_user)):
    """Return **ids** of everyone but me (frontend already has their emails/avatars)."""
    ids = await User.exclude(id=me.id).values_list("id", flat=True)
    return ids


@router.post("/{other_id}", status_code=status.HTTP_201_CREATED)
async def open_dm(other_id: int, me: User = Depends(get_current_user)):
    if other_id == me.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot DM yourself")
    other_user = await User.get_or_none(id=other_id)
    name = me.full_name.split()[-1] + "-" + other_user.full_name.split()[-1]

    async with in_transaction():
        channel, created = await Channel.get_or_create(
            name=name,
            defaults={"is_private": True},
        )

        if created:
            await ChannelMember.bulk_create([
                ChannelMember(user_id=me.id,    channel=channel),
                ChannelMember(user_id=other_id, channel=channel),
            ])

    return {"id": channel.id, "name": channel.name, "is_private": True, "repeated": not created}
