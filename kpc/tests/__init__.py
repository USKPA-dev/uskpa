from django.core.management import call_command
from model_mommy import mommy

from kpc.models import CertificateConfig
# setup model_mommy for django-localflavor
mommy.generators.add('localflavor.us.models.USZipCodeField', lambda: "00000-0000")
mommy.generators.add('localflavor.us.models.USStateField', lambda: "NY")

CERT_FORM_KWARGS = {"country_of_origin": "AQ", 'aes': 'X22222222222222',
                    'number_of_parcels': 1, 'date_of_issue': '01/01/2018',
                    'carat_weight': 1,
                    'harmonized_code': None, 'exporter': 'test',
                    'exporter_address': '123', 'consignee': 'test',
                    'consignee_address': 'test', 'shipped_value': 10,
                    'attested': True}


def load_initial_data():
    """load initial data and configuration"""
    config = CertificateConfig.get_solo()
    config.kp_countries = 'AQ'
    config.save()
    call_command('loaddata', 'initial_data', verbosity=0)
