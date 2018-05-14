import csv
from django.core.management.base import BaseCommand
from kpc.models import Licensee

# US State ID values from tblStates.csv
STATE_MAP = {'1': 'AL', '2': 'AK', '3': 'AS', '4': 'AZ',
             '5': 'AR', '6': 'CA', '7': 'CO', '8': 'CT',
             '9': 'DE', '10': 'DC', '11': 'FM', '12': 'FL',
             '13': 'GA', '14': 'GU', '15': 'HI', '16': 'ID',
             '17': 'IL', '18': 'IN', '19': 'IA', '20': 'KS',
             '21': 'KY', '22': 'LA', '23': 'ME', '24': 'MH',
             '25': 'MD', '26': 'MA', '27': 'MI', '28': 'MN',
             '29': 'MS', '30': 'MO', '31': 'MT', '32': 'NE',
             '33': 'NV', '34': 'NH', '35': 'NJ', '36': 'NM',
             '37': 'NY', '38': 'NC', '39': 'ND', '40': 'MP',
             '41': 'OH', '42': 'OK', '43': 'OR', '44': 'PW',
             '45': 'PA', '46': 'PR', '47': 'RI', '48': 'SC',
             '49': 'SD', '50': 'TN', '51': 'TX', '52': 'UT',
             '53': 'VT', '54': 'VI', '55': 'VA', '56': 'WA',
             '57': 'WV', '58': 'WI', '59': 'WY'}


class Command(BaseCommand):
    help = 'Load licensee data from csv export'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str)
        parser.add_argument('--limit', dest='limit', nargs='?', type=int)

    def handle(self, *args, **options):
        filepath = options['filepath']
        self.limit = options['limit']
        if self.limit:
            self.stdout.write(f'Limiting to {self.limit} rows.')
        self.load(filepath)

    def load(self, licensee_file):
        counter = 0
        licensee_list = []
        with open(licensee_file) as in_file:
            self.stdout.write(f'Reading data from {licensee_file}...')
            reader = csv.DictReader(in_file)
            for row in reader:
                licensee = Licensee()
                licensee.id = row['\ufeffLicenseeID']
                if licensee.id == 17:
                    self.stdout.write(f'Skipping Licensee ID 17 (TEST).')
                    continue
                licensee.name = row['LicenseeName']
                licensee.address = row['Address1']
                licensee.address2 = row['Address2']
                licensee.city = row['City']
                licensee.state = STATE_MAP[row['State']]
                licensee.zip_code = row['ZipCode5']
                licensee.tax_id = row['TaxID']

                licensee_list.append(licensee)

                counter += 1
                if self.limit and counter > self.limit:
                    break
            Licensee.objects.bulk_create(licensee_list)
            self.stdout.write(self.style.SUCCESS(
                f'Imported {counter} licensees!'))
