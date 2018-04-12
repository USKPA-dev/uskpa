from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from simple_history import register


class HistoryUser(get_user_model()):
    """
        Proxy User model here so we can register it
        with django-simple-history and necessary migrations
        are created within this app as opposed to within the
        Django auth app.
    """
    class Meta:
        proxy = True
        verbose_name = 'User'


register(HistoryUser)


class Profile(models.Model):
    """Store additional user information"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=32, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.user.username
