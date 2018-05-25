from django.conf import settings


def add_settings(request):
    """make selected settings available in templates"""
    return {'STAGE': settings.STAGE,
            'CONTACT_US': settings.CONTACT_US}
