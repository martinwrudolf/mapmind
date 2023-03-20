from django.db import models
from django.contrib.auth.models import User


class Notebook(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

class Note(models.Model):
    file_name = models.CharField(max_length=200)
    file_content = models.TextField()
    file_type = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    notebooks = models.ForeignKey(Notebook, related_name="notes", on_delete=models.CASCADE)