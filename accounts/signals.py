import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import (user_logged_in, user_logged_out,
                                         user_login_failed)
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile

User = get_user_model()

logger = logging.getLogger('accounts')


@receiver(post_save, sender=User, dispatch_uid="save_user_profile")
def update_user_profile(sender, instance, created, **kwargs):
    Profile.objects.get_or_create(user=instance)
    instance.profile.save()


@receiver(user_logged_in, sender=User, dispatch_uid='successful_login')
def successful_login(sender, request, user, **kwargs):
    logger.info(f'Successful login event for {user.username}.')


@receiver(user_logged_out, sender=User, dispatch_uid='successful_logout')
def successful_logout(sender, request, user, **kwargs):
    logger.info(f'Successful logout event for {user.username}.')


@receiver(user_login_failed, sender=None, dispatch_uid='failed_login')
def failed_login(sender, credentials, request, **kwargs):
    logger.info(f'Unsuccessful login attempt by {credentials}.')
