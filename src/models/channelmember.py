from tortoise import models, fields

class ChannelMember(models.Model):
    id        = fields.IntField(pk=True)  
    user      = fields.ForeignKeyField("models.User", related_name="memberships")  
    channel   = fields.ForeignKeyField("models.Channel", related_name="members")  
    joined_at = fields.DatetimeField(auto_now_add=True)  

    class Meta:
        table = "channel_members"
        unique_together = (("user", "channel"),)
