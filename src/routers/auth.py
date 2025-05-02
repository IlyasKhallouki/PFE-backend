from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from datetime import timedelta
from core.security import authenticate_user, create_access_token, verify_token
from schemas.token import LoginRequest, TokenResponse
from core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, response: Response):
    user = await authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,       # prevents JS access :contentReference[oaicite:8]{index=8}
        secure=True,         # only over HTTPS :contentReference[oaicite:9]{index=9}
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    return {"access_token": access_token}
