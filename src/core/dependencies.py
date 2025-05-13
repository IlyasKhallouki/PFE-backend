from fastapi import Depends, Cookie, HTTPException, status
from tortoise.exceptions import DoesNotExist

from .security import decode_access_token
from models.user import User


async def get_current_user(access_token: str = Cookie(None)) -> User:
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    payload = decode_access_token(access_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        user = await User.get(email=payload["sub"]).prefetch_related("role")
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if payload.get("jti") != user.current_jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return user

def require_admin(user = Depends(get_current_user)):
    if user.role is None or user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user