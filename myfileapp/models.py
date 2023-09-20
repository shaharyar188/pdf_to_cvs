from django.db import models

# Create your models here.
class myuploadFile(models.Model):
     myfiles=models.FileField(upload_to="")