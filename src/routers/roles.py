from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from models.role import Role
from schemas.role import RoleRead, RoleCreate
from core.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/roles", tags=["roles"])

@router.get("/")
async def list_roles():
    roles = await Role.all()
    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
        }
        for role in roles
    ]


@router.post("/add", dependencies=[Depends(require_admin)])
async def create_role(role: RoleCreate):
    if await Role.get_or_none(name=role.name):
        raise HTTPException(status_code=409, detail="Role exists")
    return await Role.create(name=role.name, description=role.description)


@router.put("/{role_id}", dependencies=[Depends(require_admin)])
async def update_role(role_id: int, role: RoleCreate):
    new_role = await Role.get_or_none(id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    new_role.name = role.name
    new_role.description = role.description
    await new_role.save()
    return new_role

@router.post("/delete/{role_id}", dependencies=[Depends(require_admin)])
async def delete_role(role_id: int):
    deleted = await Role.filter(id=role_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Role not found")