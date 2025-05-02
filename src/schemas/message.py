from pydantic import BaseModel, Field
from datetime import datetime

class MessageCreate(BaseModel):
    channel_id: int
    content: str = Field(..., min_length=1)

class MessageRead(MessageCreate):
    id: int
    author_id: int
    sent_at: datetime

    class Config:
        orm_mode = True
