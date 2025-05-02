from fastapi import Depends, Request, HTTPException, status
from core.security import verify_token
from models.user import User


async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    payload = verify_token(token)
    user = await User.get_or_none(email=payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inactive or invalid user")
    return user
