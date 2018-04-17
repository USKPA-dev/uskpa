from django.conf import settings
from django.http import HttpRequest
from django.test import TestCase
from model_mommy import mommy

from kpc.admin import LicenseeAdmin, LicenseeAdminForm
from kpc.models import Licensee


class LicenseeAdminFormTests(TestCase):

    def setUp(self):
        self.user = mommy.make(settings.AUTH_USER_MODEL)
        self.licensee_data = {'name': 'test', 'state': 'NY', 'city': 'test',
                              'address': 'test', 'zip_code': '10001',
                              'tax_id': '00-0000000'}
        self.licensee = mommy.make('Licensee')
        self.licensee.contacts.set([self.user.profile])
        self.site = 'SITE'

    def test_form_renders_with_contacts_in_initial_data(self):
        """Existing contacts are rendered on form"""
        form = LicenseeAdminForm(instance=self.licensee)
        self.assertIn(self.user.profile, form.fields['contacts'].initial)

    def test_form_save_adds_contacts(self):
        """Licensee Admin Save related method adds contacts"""
        self.licensee.contacts.set([])
        self.licensee_data.update({'contacts': [self.user.profile]})
        self.form = LicenseeAdminForm(instance=self.licensee, data=self.licensee_data)
        LicenseeAdmin(Licensee, self.site).save_related(
            request=HttpRequest(), form=self.form, formsets=[], change=True)

        self.assertIn(self.user.profile, self.licensee.contacts.all())

    def test_form_save_removes_contacts(self):
        """Licensee Admin Save related method removes contacts"""
        self.licensee_data.update({'contacts': []})
        self.form = LicenseeAdminForm(instance=self.licensee, data=self.licensee_data)
        LicenseeAdmin(Licensee, self.site).save_related(
            request=HttpRequest(), form=self.form, formsets=[], change=True)

        self.assertNotIn(self.user.profile, self.licensee.contacts.all())
