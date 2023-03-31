from django.db import models
from django.contrib.auth.models import User


class Notebook(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    vocab = models.CharField(max_length=200, null=True)
    corpus = models.CharField(max_length=200, null=True)
    kv = models.CharField(max_length=200, null=True)
    kv_vectors = models.CharField(max_length=200, null=True)

class Note(models.Model):
    file_name = models.CharField(max_length=200)
    #file_content = models.TextField()
    file_type = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    notebooks = models.ForeignKey(Notebook, related_name="notes", on_delete=models.CASCADE)
    vocab = models.CharField(max_length=200, null=True)
    corpus = models.CharField(max_length=200, null=True)