from enum import Enum
from tortoise import models, fields

class Role(str, Enum):
    admin  = "admin"
    member = "member"
    guest  = "guest"

class User(models.Model):
    """
    Tortoise-ORM model for users.
    Email is used as the unique login identifier.
    """
    id          = fields.IntField(pk=True)
    email       = fields.CharField(max_length=255, unique=True)
    hashed_pw   = fields.CharField(max_length=128)
    role        = fields.CharEnumField(Role, default=Role.member)
    is_active   = fields.BooleanField(default=True)
    created_at  = fields.DatetimeField(auto_now_add=True)
    updated_at  = fields.DatetimeField(auto_now=True)
    last_login  = fields.DatetimeField(null=True)

    class Meta:
        table = "users"
        ordering = ["id"]

    def __str__(self):
        return f"<User {self.id} {self.email}>"
