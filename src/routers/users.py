from fastapi import APIRouter, Depends, HTTPException, status
from models.user import User
from schemas.user import UserRead, UserUpdateRole, UserCreate
from core.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
async def list_users(_: User = Depends(get_current_user)):
    """Admin-only: list every user."""
    users = await User.all().prefetch_related("role")
    # return [
    #     UserRead(
    #         user.id,
    #         user.full_name,
    #         user.email,
    #         user.role
    #     ) for user in
    # ]
    return [
        {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role
        } for user in users
    ]
    
@router.post("/add", response_model=UserRead)
async def add_user(
    payload: UserCreate,
    _: User = Depends(require_admin),
):
    """Admin-only: create a new user."""
    user = await User.create(
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        role_id=payload.role_id,
    )
    return user


@router.put("/{user_id}/role", response_model=UserRead)
async def change_role(
    user_id: int,
    payload: UserUpdateRole,
    _: User = Depends(require_admin),
):
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    user.role_id = payload.role_id
    await user.save()
    return user
