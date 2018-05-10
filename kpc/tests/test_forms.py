import datetime

from django import forms
from django.conf import settings
from django.test import TestCase
from model_mommy import mommy

from kpc.forms import (CertificateRegisterForm, LicenseeCertificateForm,
                       StatusUpdateForm, VoidForm)
from kpc.models import Certificate
from kpc.tests import CERT_FORM_KWARGS


class VoidFormTests(TestCase):

    def setUp(self):
        self.form = VoidForm
        self.form_kwargs = {'reason': self.form.OTHER_CHOICE, 'void': True}

    def test_clean_notes_required_if_other(self):
        """Other, specify field must be populated if OTHER_CHOICE selected"""
        form = self.form(self.form_kwargs)
        self.assertFalse(form.is_valid())
        with self.assertRaisesRegex(forms.ValidationError, self.form.REASON_REQUIRED):
            form.clean()

    def test_save_sets_void_w_fields(self):
        """Set Certificate.void and all associated fields"""
        cert = mommy.make(Certificate)
        self.form_kwargs['reason'] = Certificate.VOID_REASONS[0]
        form = self.form(self.form_kwargs, instance=cert)
        self.assertTrue(form.is_valid())
        form.save()
        cert.refresh_from_db()
        self.assertTrue(cert.void)
        self.assertEqual(cert.notes, self.form_kwargs['reason'])
        self.assertEqual(cert.date_voided, datetime.date.today())


class StatusUpdateFormTests(TestCase):

    def setUp(self):
        self.cert = mommy.prepare(Certificate)
        self.form = StatusUpdateForm
        self.form_kwargs = {
            'next_status': Certificate.INTRANSIT, 'date': '2018-01-01'}

    def test_invalid_if_licensee_form_field_submitted(self):
        """Form fields from licensee cert form submitted, invalid"""
        self.form_kwargs['attested'] = True
        form = self.form(self.form_kwargs, instance=self.cert)
        self.assertFalse(form.is_valid())
        with self.assertRaisesRegex(forms.ValidationError, self.form.NOT_AVAILABLE):
            form.clean()

    def test_invalid_if_shipped_is_before_issued(self):
        """Shipped date must be on or after issued date"""
        self.cert.status = Certificate.PREPARED
        self.cert.date_of_issue = datetime.date.today()
        form = self.form(self.form_kwargs, instance=self.cert)
        self.assertFalse(form.is_valid())
        with self.assertRaises(forms.ValidationError):
            form.clean()

    def test_invalid_if_delivered_is_before_shipped(self):
        """Delivered date must be on or after shipped date"""
        self.cert.status = Certificate.INTRANSIT
        self.cert.date_of_shipment = datetime.date.today()
        form = self.form(self.form_kwargs, instance=self.cert)
        self.assertFalse(form.is_valid())
        with self.assertRaises(forms.ValidationError):
            form.clean()

    def test_new_status_must_be_expected(self):
        """Incoming status must match expected value from cert instance"""
        self.cert.status = Certificate.PREPARED
        self.form_kwargs['next_status'] = Certificate.DELIVERED
        form = self.form(self.form_kwargs, instance=self.cert)
        self.assertFalse(form.is_valid())
        with self.assertRaisesRegex(forms.ValidationError, form.UNEXPECTED_STATUS):
            form.clean()

    def test_intransit_and_date_set_if_valid(self):
        cert = mommy.make(Certificate, status=Certificate.PREPARED,
                          date_of_issue=datetime.date.today())
        self.form_kwargs['date'] = datetime.date.today()
        form = self.form(self.form_kwargs, instance=cert)
        self.assertTrue(form.is_valid())

        form.save()
        cert.refresh_from_db()
        self.assertEqual(cert.status, self.form_kwargs['next_status'])
        self.assertEqual(cert.date_of_shipment, datetime.date.today())

    def test_delivered_and_date_set_if_valid(self):
        cert = mommy.make(Certificate, status=Certificate.INTRANSIT,
                          date_of_shipment=datetime.date.today())
        form_kwargs = {'date': datetime.date.today(
        ), 'next_status': Certificate.DELIVERED}
        form = self.form(form_kwargs, instance=cert)
        self.assertTrue(form.is_valid())

        form.save()
        cert.refresh_from_db()
        self.assertEqual(cert.status, form_kwargs['next_status'])
        self.assertEqual(cert.date_of_delivery, datetime.date.today())


class CertificateRegistrationTests(TestCase):

    def setUp(self):
        self.licensee = mommy.make('Licensee')
        self.user = mommy.make(settings.AUTH_USER_MODEL)
        self.user.profile.licensees.add(self.licensee)
        # Valid input we expect to pass clean methods
        self.form_kwargs = {'licensee': self.licensee.id, 'contact': self.user.id,
                            'date_of_sale': '01/01/2018', 'registration_method': 'list',
                            'payment_method': 'cash',
                            'payment_amount': 20, 'cert_list': 'US1'
                            }

    def test_payment_not_expected_amount(self):
        """Payment must be # of certs * Certificate.PRICE"""
        self.form_kwargs['payment_amount'] = 1
        form = CertificateRegisterForm(self.form_kwargs)
        self.assertFalse(form.is_valid())
        self.assertIn("A payment of $20 is required. (1 requested certificates @ $20 per certificate.)",
                      [e.message for e in form.non_field_errors().data])

    def test_valid_form_no_errors_list(self):
        """Form validates w/ list data"""
        form = CertificateRegisterForm(self.form_kwargs)
        self.assertTrue(form.is_valid())

    def test_valid_form_no_errors_sequential(self):
        """Form validates w/ sequential data"""
        self.form_kwargs['payment_amount'] = 40
        form = CertificateRegisterForm(self.form_kwargs)
        self._make_sequential(1, 2)
        self.assertTrue(form.is_valid())

    def test_validation_fails_if_licensee_and_contact_dont_match(self):
        """Fail validation and provide msg if provided user is not associated with licensee"""
        self.user.profile.licensees.remove(self.licensee.id)
        form = CertificateRegisterForm(self.form_kwargs)
        valid = form.is_valid()
        self.assertIn('Contact is not associated with selected Licensee',
                      [e.message for e in form.non_field_errors().data])
        self.assertFalse(valid)

    def test_id_list_required_if_method_is_list(self):
        """Reject w/ message if cert_list isn't populated but List method is selected"""
        self.form_kwargs.pop('cert_list')
        form = CertificateRegisterForm(self.form_kwargs)
        valid = form.is_valid()
        self.assertIn("Certificate List must be provided when List method is selected.",
                      [e.message for e in form.non_field_errors().data])
        self.assertFalse(valid)

    def test_id_range_required_if_method_is_sequential(self):
        """
            Reject w/ message if cert_to & cert_from are not
            populated but sequential method is selected
        """
        self.form_kwargs.pop('cert_list')
        self.form_kwargs['registration_method'] = 'sequential'
        form = CertificateRegisterForm(self.form_kwargs)
        valid = form.is_valid()
        self.assertIn("Certificate To and From must be provided when Sequential method is selected.",
                      [e.message for e in form.non_field_errors().data])
        self.assertFalse(valid)

    def test_id_ranges_must_be_valid(self):
        """cert_from is less than or equal to cert_to"""
        self._make_sequential(25, 10)
        form = CertificateRegisterForm(self.form_kwargs)
        valid = form.is_valid()
        self.assertIn("Certificate 'To' value must be greater than or equal to 'From' value.",
                      [e.message for e in form.non_field_errors().data])
        self.assertFalse(valid)

    def test_parse_sequential(self):
        """List of sequential integers generated from provided start/end points"""
        self._make_sequential(1, 3)
        form = CertificateRegisterForm(self.form_kwargs)
        form.is_valid()
        self.assertEqual(form.get_cert_list(), [1, 2, 3])

    def test_parse_list(self):
        """List of integers returned from incoming string"""
        form = CertificateRegisterForm(self.form_kwargs)
        form.is_valid()
        self.assertEqual(form.get_cert_list(), [1])

    def _make_sequential(self, start, end):
        self.form_kwargs.pop('cert_list')
        self.form_kwargs.update(
            {'registration_method': 'sequential', 'cert_from': start, 'cert_to': end})

    def test_dupe_certificate_invalid(self):
        """
        Validation fails when requested certificates already exist
        """
        mommy.make(Certificate, number=1)
        form = CertificateRegisterForm(self.form_kwargs)
        self.assertFalse(form.is_valid())


class LicenseeCertificateFormTests(TestCase):

    def setUp(self):
        self.form_class = LicenseeCertificateForm

    def test_date_expiry_validated_against_date_issued(self):
        """
        Date of expiry must be Certificate.EXPIRY_DAYS from date of issue
        """
        kwargs = CERT_FORM_KWARGS.copy()
        kwargs['date_of_expiry'] = '12/12/9999'
        form = LicenseeCertificateForm(kwargs)
        self.assertFalse(form.is_valid())
        self.assertIn(LicenseeCertificateForm.DATE_EXPIRY_INVALID, form.errors['date_of_expiry'])
