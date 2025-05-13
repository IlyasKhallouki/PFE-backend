from fastapi import APIRouter, Response, HTTPException, status, Depends
from uuid import uuid4

from core.security import verify_password, create_access_token
from models.user import User
from schemas.token import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, resp: Response):
    user = await User.get_or_none(email=payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    await user.fetch_related("role") 
    jti = str(uuid4())
    user.current_jti = jti
    await user.save()

    token = create_access_token(user.email, user.role.name if user.role else None, jti)
    resp.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24,
    )
    return TokenResponse(access_token=token)