from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from simple_history.models import HistoricalRecords
from simple_history import register


from kpc.models import Certificate, Licensee


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
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=32, blank=True)
    licensees = models.ManyToManyField(
        'kpc.Licensee', blank=True, related_name='contacts')

    history = HistoricalRecords()

    class Meta:
        permissions = (
            ('can_review_certificates', "Can Review all Certificates"),
        )

    def __str__(self):
        return self.get_user_display_name()

    def get_user_display_name(self):
        """User's fullname or username"""
        return self.user.get_full_name() or self.user.get_username()

    def get_licensees(self):
        """List of licensees to which this user has access"""
        if self.user.is_superuser or self.is_auditor:
            return Licensee.objects.all()
        return self.licensees.filter(is_active=True)

    def get_address_book_url(self):
        """URL to display as address book nav link"""
        try:
            return self.licensees.get().get_absolute_url()
        except (Licensee.MultipleObjectsReturned, Licensee.DoesNotExist):
            return None

    @property
    def is_auditor(self):
        return self.user.has_perm('accounts.can_review_certificates') \
               and not self.user.is_superuser

    def certificates(self):
        """Certificates which this user may access"""
        if self.user.is_superuser or self.is_auditor:
            return Certificate.objects.all()
        else:
            return Certificate.objects.filter(licensee__in=self.get_licensees())
