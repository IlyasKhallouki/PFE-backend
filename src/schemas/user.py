from pydantic import BaseModel


class UserRead(BaseModel):
    id: int
    full_name: str
    email: str
    role: str | None

    class Config:
        orm_mode = True
        
    def __init__(self, id, full_name, email, role):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.role = role


class UserUpdateRole(BaseModel):
    role_id: int
