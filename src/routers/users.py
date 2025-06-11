from fastapi import APIRouter, Depends, HTTPException, status
from models.user import User
from models.role import Role
from schemas.user import UserRead, UserUpdateRole, UserCreate
from core.dependencies import get_current_user, require_admin
from core.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
async def list_users(_: User = Depends(get_current_user)):
    """List all users"""
    users = await User.all().prefetch_related("role")
    
    return [
        {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role.name if user.role else None
        } 
        for user in users
    ]
    
@router.post("/add")
async def add_user(
    payload: UserCreate,
    _: User = Depends(require_admin),
):
    """Admin-only: create a new user."""
    user = await User.create(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role_id=payload.role_id,
    )
    role = await Role.get_or_none(id=payload.role_id)
    role_name = role.get if role else None
    
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": role_name,
    } 
    
@router.put("/{user_id}")
async def update_user(
    user_id: int,
    payload: UserCreate,
    _: User = Depends(require_admin),
):
    """Admin-only: update a user."""
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    user.full_name = payload.full_name
    user.email = payload.email
    user_role = await Role.get_or_none(id=payload.role_id)
    user.role = user_role
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    await user.save()
    return user
    
@router.post("/delete/{user_id}/")
async def delete_user(
    user_id: int,
    _: User = Depends(require_admin),
):
    """Admin-only: delete a user."""
    deleted = await User.filter(id=user_id).delete()
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return {"detail": "User deleted"}


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
