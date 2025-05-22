from pydantic import BaseModel


class RoleRead(BaseModel):
    id: int
    name: str
    description: str | None

    class Config:
        orm_mode = True
        
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description
 
 
class RoleCreate(BaseModel):
    name: str
    description: str | None = None
