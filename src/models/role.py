from tortoise import fields, models
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .channel import Channel

class Role(models.Model):
    id: int = fields.IntField(pk=True)
    name: str = fields.CharField(max_length=32, unique=True)
    description: str | None = fields.CharField(max_length=255, null=True)

    users: fields.ReverseRelation["User"] 
    channels: fields.ReverseRelation["Channel"] 

    class Meta:
        table = "roles"

    def __str__(self) -> str:  
        return self.name