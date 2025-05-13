from tortoise import fields, models
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # for Pylance autocomplete only
    from .channelmember import ChannelMember
    from .message import Message
    from .role import Role


class User(models.Model):
    id: int = fields.IntField(pk=True)

    # NEW
    full_name: str = fields.CharField(max_length=120)

    email: str = fields.CharField(max_length=120, unique=True)
    hashed_password: str = fields.CharField(max_length=128)

    role: fields.ForeignKeyNullableRelation["Role"] = fields.ForeignKeyField(
        "models.Role", related_name="users", null=True
    )
    current_jti: str | None = fields.CharField(max_length=36, null=True)

    is_active: bool = fields.BooleanField(default=True)
    last_login: str = fields.DatetimeField(auto_now=True)

    messages: fields.ReverseRelation["Message"]
    channel_memberships: fields.ReverseRelation["ChannelMember"]

    class Meta:
        table = "users"

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"
