from django.db import models
import uuid
# Create your models here.
class agent_clients(models.Model):
    id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    appointment_scheduled = models.DateTimeField(max_length=255,blank=True, null=True)
    product = models.CharField(max_length=200, null=True,blank=True)
    name = models.CharField(max_length=200, null=True,blank=True)
    surname = models.CharField(max_length=200, null=True,blank=True)
    gender = models.CharField(max_length=200, null=True,blank=True)
    phone_number = models.CharField(max_length=200, null=True,blank=True)
    source = models.CharField(max_length=200, null=True,blank=True)
    age = models.IntegerField(null=True,blank=True)
    def __str__(self):
        return self.name