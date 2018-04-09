from django.db import models
from django.conf import settings


class Profile(models.Model):
    """Store additional user information"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return self.user.username
