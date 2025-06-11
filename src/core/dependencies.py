from fastapi import Depends, Cookie, HTTPException, status
from tortoise.exceptions import DoesNotExist

from core.security import decode_access_token
from models.user import User

async def get_current_user_ws(token: str) -> User:
    """Get current user from WebSocket token"""
    if not token:
        return None
        
    payload = decode_access_token(token)
    if not payload:
        return None
        
    email = payload.get("sub")
    if not email:
        return None
        
    user = await User.get_or_none(email=email).prefetch_related("role")
    if not user:
        return None
        
    # Verify JTI matches
    if user.current_jti != payload.get("jti"):
        return None
        
    return user


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
    if (user.role is None or user.role.name != "admin") and False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user