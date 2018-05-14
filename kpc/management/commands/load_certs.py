import csv
import io
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django_countries import countries
from django_countries.fields import Country

from kpc.models import Certificate, Licensee, PortOfExport

EXPECTED_DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'

# Map HScode to objects from initial-data.json
HSCODE_MAP = {'3': 2, '4': 1, '6': 3}

# Map status codes to Certificate attributes
STATUS_MAP = {'2': Certificate.PREPARED,
              '3': Certificate.DELIVERED, '4': Certificate.INTRANSIT}

# relative path from manage.py to the refCountries.csv file
COUNTRY_CSV = './data/refCountries.csv'


class Command(BaseCommand):
    help = 'Load certificate data from csv export'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str)
        parser.add_argument('--limit', dest='limit', nargs='?', type=int)

    def handle(self, *args, **options):
        filepath = options['filepath']
        self.limit = options['limit']
        if self.limit:
            self.stdout.write(f'Limiting to {self.limit} rows.')

        self.stdout.write(f'Reading data from {filepath}...')
        self.rectified_csv = rectify_csv(filepath)
        self.stdout.write("Newlines converted to '|'")

        self.licensee_id_list = list(
            Licensee.objects.all().values_list('id', flat=True))
        self.port_of_export_map = {
            poe.name: poe.id for poe in PortOfExport.objects.all()}

        self.stdout.write(f"Reading country data from {COUNTRY_CSV}...")
        self.countries = build_country_map()

        self.load_certs(filepath)

    def get_country(self, value):
        """Get Country object for incoming country value"""
        value = ignore_null_str(value)
        if value:
            value = self.countries[value]
            value = Country(code=value)
        return value

    def load_certs(self, cert_file):
        self.counter = 0
        self.test_excluded = 0
        cert_list = []

        reader = csv.DictReader(self.rectified_csv)
        for row in reader:
            self.counter += 1
            if self.limit and self.counter > self.limit:
                break

            cert = self.make_certificate(row)
            if cert:
                cert_list.append(cert)
        Certificate.objects.bulk_create(cert_list)

        self.stdout.write(self.style.SUCCESS(
            f'Processed {self.counter} certificate records.'))
        self.stdout.write(self.style.SUCCESS(
            f'Excluded {self.test_excluded} certificates with Licensee: TEST'))
        self.stdout.write(self.style.SUCCESS(
            f'Imported {self.counter-self.test_excluded} certificates!'))

    def make_certificate(self, row):
        """Parse CSV row into Certificate object"""
        cert = Certificate()
        cert.number = prepare_number(row['CertNumber'])

        licensee_id = int(row['LicenseeID'])
        # Ignore TEST(17) licensee records
        if licensee_id == 17:
            self.test_excluded += 1
            return
        if licensee_id in self.licensee_id_list:
            cert.licensee_id = licensee_id
        else:
            self.stdout.write(self.style.WARNING(
                f"{cert}: Could not find Licensee ({licensee_id}), setting to None"))

        try:
            cert.aes = prepare_aes(row['AESNUmber'])
            if cert.aes:
                validate_aes(cert.aes)
        except ValidationError:
            pass
            self.stdout.write(self.style.WARNING(
                f"{cert}: Invalid AES: ({cert.aes}) importing as-is."))

        poe = prepare_poe(row['PortOfExport'])
        if poe:
            try:
                cert.port_of_export_id = self.port_of_export_map[poe]
            except KeyError:
                self.stdout.write(self.style.WARNING(
                    f"{cert}: Unknown Port of Export: ({poe}) setting to None"))

        cert.void = prepare_boolean(row['VoidCert'])
        cert.date_voided = prepare_date(row['VoidDate'])
        cert.notes = ignore_null_str(row['VoidComment'])

        status_id = ignore_null_str(row['DeliveryStatusID'])
        if not status_id and cert.void:
            cert.status = Certificate.VOID
        elif not status_id:
            cert.status = Certificate.ASSIGNED
        else:
            try:
                cert.status = STATUS_MAP[status_id]
            except KeyError:
                self.stdout.write(self.style.WARNING(
                    f"{cert}: Could not parse Status ({status_id})"))
        try:
            cert.harmonized_code_id = prepare_hscode(row['HCDCodeID'])
        except KeyError:
            self.stdout.write(self.style.WARNING(
                f"{cert}: Could not parse HSCode ({row['HCDCodeID']}), setting to None"))

        cert.consignee = ignore_null_str(row['Importer'])
        cert.consignee_address = prepare_address(
            row['ImporterAddress'])

        try:
            consignee_country = self.get_country(
                row['ImporterCountry'])
        except KeyError:
            self.stdout.write(self.style.WARNING(
                f"{cert}: Could not find Country ID ({row['ImporterCountry']}), setting to None"))
            consignee_country = None

        # add country to consignee address
        if consignee_country and \
                not cert.consignee_address.endswith(consignee_country.name):
            cert.consignee_address += f'\n{consignee_country.name}'

        cert.shipped_value = prepare_decimal(row['ShippedValue'])
        cert.date_of_sale = prepare_date(row['DateOfSale'])
        cert.date_of_issue = prepare_date(row['DateOfIssue'])
        cert.date_of_expiry = prepare_date(row['DateOfExpiry'])
        cert.date_of_delivery = prepare_date(row['DeliveryDate'])
        cert.date_of_shipment = prepare_date(row['ShipDate'])
        cert.number_of_parcels = ignore_null(row['NumberOfParcels'])
        cert.carat_weight = ignore_null(row['CaratWeight'])
        return cert


def rectify_csv(filepath):
    """
    Input CSV contains newlines embedded in address fields
    Identify these newlines and replace them
    with `|` characters.

    The values of the first column have a known and expected format
    An integer primary key value, followed by a 'US\d.' Certificate Identifier
    regex; '/\d.,US/'

    We use this information to identify offending newlines
    Regex below captures new lines which are NOT followed
    by the expected integer PK and Certificate identifier fields
    """
    pattern = re.compile(r'''
                        (\n)       # Capture new-line for replacement
                        (?!        # Negative look ahead
                            \d+     # One or more digit
                            ,       # CSV field separator
                            US|$    # 'US' portion of expected following field OR end of line
                        )
                        ''', re.VERBOSE)
    output = io.StringIO()
    with open(filepath) as infile:
        f = infile.read()
        result = pattern.sub('|', f)
        output.write(result)
    output.seek(0)
    return output


# data migration transformations
def validate_aes(value):
    validator = Certificate._meta.get_field('aes').validators[0]
    validator(value)


def prepare_poe(value):
    """Harmonize incoming Port of Export"""
    if value == 'NULL':
        value = ''
    elif value == 'Cincinnati(OH)':
        value = 'Cincinnati (OH)'
    elif value == 'New York (NY)':
        value = 'New York (JFK)'
    elif value in ('Memphis, TN', 'Memphis,TN', '2095 Memphis, TN'):
        value = 'Memphis (TN)'
    elif value == 'Newark, NJ':
        value = 'Newark (NJ)'
    elif value in ('Louisville, KY'):
        value = 'Louisville (KY)'
    elif value == 'Detroit, MI':
        value = 'Detroit (MI)'
    elif value == 'Philadelphia, PA':
        value = 'Philadelphia (PA)'
    elif value == 'Honolulu, HA':
        value = 'Honolulu (HA)'
    elif value == 'Indianapolis, IN':
        value = 'Indianapolis (IN)'

    value = value.replace('  ', ' ')

    return value


def prepare_aes(value):
    pattern = re.compile('\d{14}')
    if value == 'NULL':
        value = ''
    value = value.replace('x', 'X')
    # Check if we're only missing the leading X
    missing_x = pattern.match(value)
    if missing_x:
        value = 'X' + value
    return value


def preprocess_country(value):
    """
    Convert legacy Country names to DJANGO_COUNTRIES
    ready ISO-3166 values
    """

    if value == "People's Republic of China":
        value = 'China'
    elif value == "Democratic Republic of Congo":
        value = 'Congo (the Democratic Republic of the)'
    elif value == 'Republic of Congo':
        value = 'Congo'
    elif value == 'Lao Peoples Republic':
        value = "Laos"
    elif value == 'Russian Federation':
        value = 'Russia'
    elif value == 'Viet Nam':
        value = 'Vietnam'
    elif value == 'Republic of Korea':
        value = 'South Korea'
    elif value == 'Czech Republic':
        value = 'Czechia'
    elif value in ('Ivory Coast(banned)', 'Ivory Coast (banned)'):
        value = "Côte d'Ivoire"
    elif value == 'UK':
        value = 'United Kingdom'
    return value


def build_country_map():
    """Map legacy country PK to ISO 3166 two letter code"""
    mapped_countries = {}
    dj_countries = {name: code for code, name in countries}
    with open(COUNTRY_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            country = preprocess_country(row['CountryName'])
            dj_country = dj_countries[country]
            mapped_countries.update({row['\ufeffID']: dj_country})
    return mapped_countries


def prepare_hscode(value):
    if value != 'NULL':
        return HSCODE_MAP[value]


def prepare_boolean(value):
    if value == 'NULL':
        value = None
    return bool(value)


def ignore_null(value):
    if value == 'NULL':
        return None
    return value


def ignore_null_str(value):
    if value == 'NULL':
        return ''
    return value


def prepare_number(cert_number):
    """Convert incoming CertNumber field to Certificate.number"""
    return int(cert_number[2:])


def prepare_decimal(value):
    if value != 'NULL':
        try:
            return Decimal(value)
        except InvalidOperation:
            pass


def prepare_date(value):
    value = ignore_null(value)
    if value:
        try:
            dt = datetime.strptime(value, EXPECTED_DATE_FORMAT).date()
            return dt
        except ValueError:
            print(f'Could not parse date: {value}')


def prepare_address(value):
    value = ignore_null_str(value)
    if value:
        # '|' was a placeholder for new-lines
        value = value.replace('|', '\n')
    return value
