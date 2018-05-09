from django.core.management import call_command
from model_mommy import mommy

# setup model_mommy for django-localflavor
mommy.generators.add('localflavor.us.models.USZipCodeField', lambda: "00000-0000")
mommy.generators.add('localflavor.us.models.USStateField', lambda: "NY")

CERT_FORM_KWARGS = {"country_of_origin": "AQ", 'aes': 'X22222222222222',
                    'number_of_parcels': 1, 'date_of_issue': '01/01/2018',
                    'carat_weight': 1,
                    'harmonized_code': '7102.31', 'exporter': 'test',
                    'exporter_address': '123', 'consignee': 'test',
                    'consignee_address': 'test', 'shipped_value': 10,
                    'attested': True}


def load_groups():
    """load groups and permissions"""
    call_command('loaddata', 'groups', verbosity=0)
