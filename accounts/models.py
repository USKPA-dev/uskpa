from django.conf import settings
from django.db import models

from kpc.models import Certificate, Licensee


class Profile(models.Model):
    """Store additional user information"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=32, blank=True)
    licensees = models.ManyToManyField(
        'kpc.Licensee', blank=True, related_name='contacts')

    class Meta:
        permissions = (
            ('can_review_certificates', "Can Review all Certificates"),
            ('can_review_edit_requests', "Can Review Certificate Edit Requests"),
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

    def _is_group_member(self, group):
        """Check if user is member of specified group"""
        return self.user.groups.filter(name=group).exists()

    @property
    def is_auditor(self):
        return self._is_group_member('Auditor')

    @property
    def is_reviewer(self):
        return self._is_group_member('Reviewer')

    def can_edit_certs(self):
        """User may prepare, void, or update the status of certificates"""
        return not any([self.is_auditor, self.is_reviewer])

    def certificates(self):
        """Certificates which this user may access"""
        if self.user.has_perm('accounts.can_review_certificates') or self.is_auditor:
            return Certificate.objects.all()
        else:
            return Certificate.objects.filter(licensee__in=self.get_licensees())
