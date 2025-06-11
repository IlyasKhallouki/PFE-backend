from fastapi import APIRouter, Response, HTTPException, status, Request, Depends
from uuid import uuid4

from core.security import verify_password, create_access_token
from models.user import User
from schemas.token import LoginRequest, TokenResponse
from core.dependencies import get_current_user

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


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role.name if current_user.role else None
    }
    
@router.post("/logout")
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    """Logout current user"""
    # Invalidate the current JWT
    current_user.current_jti = None
    await current_user.save()
    
    # Clear the cookie
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    return {"detail": "Successfully logged out"}

@router.get("/bot-info")
async def get_bot_info(request: Request, _: User = Depends(get_current_user)):
    """
    Returns the user ID and name of the chatbot.
    """
    bot_id = request.app.state.chatbot_user_id
    return {"id": bot_id, "full_name": "Chatbot"}