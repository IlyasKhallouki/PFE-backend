from tortoise import fields, models
from models.role import Role

class Channel(models.Model):
    id: int = fields.IntField(pk=True)
    name: str = fields.CharField(max_length=60)
    is_private: bool = fields.BooleanField(default=False)

    role: fields.ForeignKeyNullableRelation[Role] = fields.ForeignKeyField(
        "models.Role", related_name="channels", null=True
    )

    members: fields.ReverseRelation["ChannelMember"] # type: ignore[name-defined]
    messages: fields.ReverseRelation["Message"] # type: ignore[name-defined]

    class Meta:
        unique_together = ("name", "is_private")
        table = "channels"

    def __str__(self) -> str: 
        return self.name