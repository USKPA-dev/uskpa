from django.conf import settings
from django.http import HttpRequest
from django.test import TestCase
from model_mommy import mommy

from kpc.admin import CertificateAdminForm, LicenseeAdmin, LicenseeAdminForm
from kpc.models import Certificate, Licensee


class CertificateAdminFormTests(TestCase):

    def setUp(self):
        self.data = {'number': 1, 'status': Certificate.AVAILABLE,
                     'date_of_issue': '2018-01-01', 'date_of_sale': '2018-01-01',
                     'date_of_shipment': '2018-01-01', 'date_of_delivery': '2018-01-01'}

    def test_form_clean_valid(self):
        """All occur on same day is valid"""
        form = CertificateAdminForm(self.data)
        self.assertTrue(form.is_valid())

    def test_sold_required_for_issue(self):
        self.data.update({'date_of_sale': None})
        form = CertificateAdminForm(self.data)
        self.assertFalse(form.is_valid())

    def test_issued_required_for_shipment(self):
        self.data.update({'date_of_issue': None})
        form = CertificateAdminForm(self.data)
        self.assertFalse(form.is_valid())

    def test_shipped_required_for_delivery(self):
        self.data.update({'date_of_shipment': None})
        form = CertificateAdminForm(self.data)
        self.assertFalse(form.is_valid())

    def test_only_issued(self):
        """Dates may be partially populated"""
        self.data.update({'date_of_shipment': None, 'date_of_delivery': None})
        form = CertificateAdminForm(self.data)
        self.assertTrue(form.is_valid())

    def test_issued_before_sold(self):
        self.data.update({'date_of_issue': "2000-01-01"})
        form = CertificateAdminForm(self.data)
        self.assertFalse(form.is_valid())

    def test_shipped_before_issued(self):
        self.data.update({'date_of_shipment': "2000-01-01"})
        form = CertificateAdminForm(self.data)
        self.assertFalse(form.is_valid())

    def test_delivered_before_shipped(self):
        self.data.update({'date_of_delivery': "2000-01-01"})
        form = CertificateAdminForm(self.data)
        self.assertFalse(form.is_valid())


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
        self.form = LicenseeAdminForm(
            instance=self.licensee, data=self.licensee_data)
        LicenseeAdmin(Licensee, self.site).save_related(
            request=HttpRequest(), form=self.form, formsets=[], change=True)

        self.assertIn(self.user.profile, self.licensee.contacts.all())

    def test_form_save_removes_contacts(self):
        """Licensee Admin Save related method removes contacts"""
        self.licensee_data.update({'contacts': []})
        self.form = LicenseeAdminForm(
            instance=self.licensee, data=self.licensee_data)
        LicenseeAdmin(Licensee, self.site).save_related(
            request=HttpRequest(), form=self.form, formsets=[], change=True)

        self.assertNotIn(self.user.profile, self.licensee.contacts.all())
