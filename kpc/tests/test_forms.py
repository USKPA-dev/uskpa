from django.conf import settings
from django.test import TestCase
from model_mommy import mommy
from kpc.forms import CertificateRegisterForm


class CertificateRegistrationTests(TestCase):

    def setUp(self):
        self.licensee = mommy.make('Licensee')
        self.user = mommy.make(settings.AUTH_USER_MODEL)
        self.user.profile.licensees.add(self.licensee)
        # Valid input we expect to pass clean methods
        self.form_kwargs = {'licensee': self.licensee.id, 'contact': self.user.id,
                            'date_of_issue': '01/01/2018', 'registration_method': 'list',
                            'payment_method': 'cash',
                            'payment_amount': 1, 'cert_list': 'US1'
                            }

    def test_valid_form_no_errors(self):
        """Form validates"""
        form = CertificateRegisterForm(self.form_kwargs)
        valid = form.is_valid()
        self.assertTrue(valid)

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
        self.form_kwargs.pop('cert_list')
        self.form_kwargs.update({'registration_method': 'sequential', 'cert_from': 25, 'cert_to': 10})
        form = CertificateRegisterForm(self.form_kwargs)
        valid = form.is_valid()
        self.assertIn("Certificate 'To' value must be greater than or equal to 'From' value.",
                      [e.message for e in form.non_field_errors().data])
        self.assertFalse(valid)

    def test_parse_sequential(self):
        """List of sequential integers generated from provided start/end points"""
        self.form_kwargs.pop('cert_list')
        self.form_kwargs.update(
            {'registration_method': 'sequential', 'cert_from': 1, 'cert_to': 3})
        form = CertificateRegisterForm(self.form_kwargs)
        form.is_valid()
        self.assertEqual(form.get_cert_list(), [1, 2, 3])

    def test_parse_list(self):
        """List of integers returned from incoming string"""
        form = CertificateRegisterForm(self.form_kwargs)
        form.is_valid()
        self.assertEqual(form.get_cert_list(), [1])
