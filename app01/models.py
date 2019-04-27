from django.db import models

class ESTotal(models.Model):
    a_url = models.CharField(max_length=128)
    title = models.CharField(max_length=128)
    summary = models.CharField(max_length=1280)
    action_type = models.CharField(max_length=12)
