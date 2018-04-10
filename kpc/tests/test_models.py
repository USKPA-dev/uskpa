from django.test import SimpleTestCase
from django.core.exceptions import ValidationError

from model_mommy import mommy

from kpc.models import Licensee


# setup model_mommy for django-localflavor
def _gen_zipcode():
    return "00000-0000"


def _gen_state():
    return 'NY'


mommy.generators.add('localflavor.us.models.USZipCodeField', _gen_zipcode)
mommy.generators.add('localflavor.us.models.USStateField', _gen_state)


class LicenseeTests(SimpleTestCase):

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
