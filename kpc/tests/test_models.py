from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from model_mommy import mommy

from kpc.models import Certificate, Licensee
from kpc.tests import load_initial_data


class LicenseeTests(TestCase):

    def setUp(self):
        self.licensee = mommy.prepare(Licensee)

    def test_licensee_returns_name_str(self):
        """String representation of name is model's name value"""
        self.assertEqual(str(self.licensee), self.licensee.name)

    def test_bad_tin_rejection(self):
        """Reject bad tax identifiers"""
        with self.assertRaises(ValidationError):
            self.licensee.tax_id = 'NOT A TIN'
            self.licensee.clean_fields()

    def test_valid_tin_acceptance(self):
        """Properly formatted tax identifiers do not raise ValidationErrors"""
        self.licensee.tax_id = '12-1234567'
        self.licensee.clean_fields()

    def test_superuser_can_access(self):
        """Can access details if admin"""
        superuser = mommy.make(settings.AUTH_USER_MODEL, is_superuser=True)
        self.assertTrue(self.licensee.user_can_access(superuser))

    def test_auditor_can_access(self):
        """Can access details if auditor"""
        load_initial_data()
        auditor = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        auditor.groups.add(Group.objects.get(name='Auditor'))
        self.assertTrue(self.licensee.user_can_access(auditor))

    def test_contact_can_access(self):
        """Can access details if contact of licensee"""
        contact = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        self.licensee.save()
        contact.profile.licensees.add(self.licensee)
        self.assertTrue(self.licensee.user_can_access(contact))

    def test_unaffiliated_user_cannot_access(self):
        """Cannot access details as un-affiliated user"""
        other_user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        self.assertFalse(self.licensee.user_can_access(other_user))


class CertificateTests(TestCase):

    def setUp(self):
        self.cert = mommy.make(Certificate, number=1)

    def test_save_sets_last_modified(self):
        """Last modified set on object creation"""
        cert = mommy.prepare(Certificate, last_modified=None)
        cert.save()
        self.assertIsNotNone(cert.last_modified)

    def test_last_modified_updated_for_existing_objects(self):
        """Last modified set on existing object update"""
        cert = mommy.make(Certificate, last_modified=None)
        orig_modified = cert.last_modified
        cert.save()
        cert.refresh_from_db()
        self.assertNotEqual(orig_modified, cert.last_modified)

    def test_display_name(self):
        """Certificates displays as 'US{number}"""
        self.assertEqual(str(self.cert), f'US{self.cert.number}')

    def test_bad_aes_rejection(self):
        """Reject malformed AES identifiers"""
        with self.assertRaises(ValidationError):
            self.cert.aes = 'X15152'
            self.cert.clean_fields()

    def test_accept_valid_aes_rejection(self):
        """Accept valid AES identifiers
            regex: X\d{14}
        """
        self.cert.aes = 'X12345678901234'
        self.cert.clean_fields()

    def test_next_available_when_no_certs(self):
        """Next available cert number is 1 if no certs exist"""
        self.cert.delete()
        self.assertEquals(Certificate.next_available_number(), 1)

    def test_next_available_when_certs(self):
        """Next available cert number is highest existing+1"""
        self.assertEquals(Certificate.next_available_number(), 2)

    def test_default_search_filters_returns_query_params(self):
        user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        """Query parameters for default cert search are generated"""
        expected = 'status=0&status=1&status=2'
        self.assertEqual(Certificate.default_search_filters(user), expected)

    def test_default_auditor_search_filters_returns_query_params(self):
        load_initial_data()
        auditor = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        auditor.groups.add(Group.objects.get(name='Auditor'))
        """Query parameters for default auditor cert search are generated"""
        expected = 'status=1&status=2&status=3'
        self.assertEqual(Certificate.default_search_filters(auditor), expected)

    def test_status_not_modifiable(self):
        """
           Certificate status is NOT user moddable status it
           not PREPARED or SHIPPED
        """
        self.cert.status = Certificate.AVAILABLE
        self.assertFalse(self.cert.status_can_be_updated)
        self.cert.status = Certificate.DELIVERED
        self.assertFalse(self.cert.status_can_be_updated)
        self.cert.status = Certificate.VOID
        self.assertFalse(self.cert.status_can_be_updated)

    def test_status_modifiable(self):
        """certificate status is user moddable if its PREPARED or SHIPPED"""
        self.cert.status = Certificate.PREPARED
        self.assertTrue(self.cert.status_can_be_updated)
        self.cert.status = Certificate.SHIPPED
        self.assertTrue(self.cert.status_can_be_updated)

    def test_next_status_label_returns_none(self):
        """No next status label if not user moddable"""
        self.assertIsNone(self.cert.next_status_label)
        self.cert.status = Certificate.VOID
        self.assertIsNone(self.cert.next_status_label)

    def test_next_status_label(self):
        """Return display value next status value"""
        self.cert.status = Certificate.PREPARED
        self.assertEqual(self.cert.next_status_label, 'Shipped')

    def test_next_status_value(self):
        """Return integer of next status"""
        self.cert.status = Certificate.PREPARED
        self.assertEqual(self.cert.next_status_value, Certificate.SHIPPED)


class ReceiptTests(TestCase):

    def test_receipt_number_starts_at_default(self):
        """Receipt.number starts at settings.LAST_RECEIPT_NUMBER"""
        receipt = mommy.make('Receipt')
        self.assertEqual(receipt.number, settings.LAST_RECEIPT_NUMBER)

    def test_receipt_number_increments_from_default(self):
        """Receipt.number starts at settings.LAST_RECEIPT_NUMBER and increments by 1"""
        mommy.make('Receipt')
        receipt = mommy.make('Receipt')

        self.assertEqual(receipt.number, settings.LAST_RECEIPT_NUMBER + 1)

    def test_receipt_number_unchanged_by_update(self):
        """Receipt.number unchanged by update to existing instance"""
        receipt = mommy.make('Receipt')
        self.assertEqual(receipt.number, settings.LAST_RECEIPT_NUMBER)
        receipt.licensee_name = 'UPDATED'
        receipt.save()
        receipt.refresh_from_db()
        self.assertEqual(receipt.number, settings.LAST_RECEIPT_NUMBER)
