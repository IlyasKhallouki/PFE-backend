from tortoise import models, fields

class Message(models.Model):
    id       = fields.IntField(pk=True)  
    author   = fields.ForeignKeyField("models.User", related_name="messages")  
    channel  = fields.ForeignKeyField("models.Channel", related_name="messages")  
    content  = fields.TextField()  
    sent_at  = fields.DatetimeField(auto_now_add=True)  

    class Meta:
        table = "messages"
        ordering = ["-sent_at"]
