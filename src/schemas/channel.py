from pydantic import BaseModel, Field

class ChannelCreate(BaseModel):
    name: str = Field(..., max_length=64)
    is_private: bool = False

class ChannelRead(ChannelCreate):
    id: int

    class Config:
        orm_mode = True
