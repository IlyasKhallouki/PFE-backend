from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from models.role import Role
from core.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/roles", tags=["roles"])





@router.get("/", response_model=List[str], dependencies=[Depends(require_admin)])
async def list_roles():
    return [r.name async for r in Role.all()]


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
async def create_role(name: str, description: str | None = None):
    if await Role.get_or_none(name=name):
        raise HTTPException(status_code=409, detail="Role exists")
    return await Role.create(name=name, description=description)


@router.delete("/{role_id}", dependencies=[Depends(require_admin)])
async def delete_role(role_id: int):
    deleted = await Role.filter(id=role_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found")