from tortoise import models, fields

class Channel(models.Model):
    id         = fields.IntField(pk=True)  
    name       = fields.CharField(max_length=64, unique=True)  
    is_private = fields.BooleanField(default=False)  
    created_at = fields.DatetimeField(auto_now_add=True)  

    class Meta:
        table = "channels"
        ordering = ["name"]
