from django.conf import settings


def contact_email(request):
    return {'CONTACT_US': settings.CONTACT_US}
