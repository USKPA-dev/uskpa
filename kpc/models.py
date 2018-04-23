from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.http import QueryDict
from django_countries.fields import CountryField
from localflavor.us.models import USStateField, USZipCodeField
from simple_history.models import HistoricalRecords


class Licensee(models.Model):
    """
    An entity involved in the export/import of rough diamonds
    within the United States
    """
    name = models.CharField(max_length=256)
    address = models.CharField(max_length=1024)
    address2 = models.CharField(verbose_name='Address continued',
                                max_length=1024, blank=True)
    city = models.CharField(max_length=1024)
    state = USStateField()
    zip_code = USZipCodeField()
    tax_id = models.CharField(max_length=10,
                              help_text='Tax Identification Number',
                              validators=[
                                  RegexValidator(regex='\d{2}-\d{7}',
                                                 message='TIN format: ##-#######'
                                                 )
                                        ]
                              )

    history = HistoricalRecords()

    def __str__(self):
        return self.name


class Certificate(models.Model):
    ASSIGNED = 0
    PREPARED = 1
    INTRANSIT = 2
    DELIVERED = 3
    VOID = 4

    DEFAULT_SEARCH = [ASSIGNED, PREPARED, INTRANSIT]

    STATUS_CHOICES = (
        (ASSIGNED, 'Assigned'),
        (PREPARED, 'Prepared'),
        (INTRANSIT, 'In-transit'),
        (DELIVERED, 'Delivered'),
        (VOID, 'Void')
    )

    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('check', 'Check'),
    )

    HS_CODE_CHOICES = (
        ('7102.10', '7102.10'),
        ('7102.21', '7102.21'),
        ('7102.29', '7102.29'),
        ('7102.31', '7102.31'),
        ('7102.39', '7102.39'),
    )

    # Fields on physical certificate
    number = models.PositiveIntegerField(help_text='USKPA Certificate ID number', unique=True)
    aes = models.CharField(max_length=15,
                           blank=True,
                           help_text='AES Confirmation Number (ITN)',
                           validators=[
                                RegexValidator(regex='X\d{14}',
                                               message='AES Confirmation (ITN) format: X##############'
                                               )
                                    ]
                           )
    country_of_origin = CountryField(blank=True)
    date_of_issue = models.DateTimeField(blank=True, null=True, help_text='Date of Issue')
    date_of_expiry = models.DateTimeField(blank=True, null=True, help_text='Date of Expiry')
    shipped_value = models.DecimalField(max_digits=20, decimal_places=2,
                                        blank=True, null=True, help_text="Value in USD")
    exporter = models.CharField(blank=True, max_length=256)
    exporter_address = models.TextField(blank=True)
    number_of_parcels = models.PositiveIntegerField(blank=True, null=True)
    consignee = models.CharField(blank=True, max_length=256, help_text='Ultimate Consignee Name')
    consignee_address = models.TextField(blank=True, help_text='Ultimate Consignee Address')
    carat_weight = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True)
    harmonized_code = models.CharField(choices=HS_CODE_CHOICES, max_length=32,
                                       blank=True)

    # Non certificate fields
    assignor = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT)
    licensee = models.ForeignKey('Licensee', blank=True, null=True, on_delete=models.PROTECT)
    status = models.IntegerField(choices=STATUS_CHOICES, default=ASSIGNED)
    last_modified = models.DateTimeField(auto_now=True)
    date_of_sale = models.DateTimeField(blank=True, null=True, help_text='Date of sale to licensee')
    payment_method = models.CharField(choices=PAYMENT_METHOD_CHOICES, max_length=5,
                                      blank=True)
    void = models.BooleanField(default=False, help_text="Certificate has been voided?")
    notes = models.TextField(blank=True)
    # port_of_export = models.ForeignKey('PortOfExport', blank=True, on_delete=models.PROTECT)

    history = HistoricalRecords()

    class Meta:
        get_latest_by = ('number', )

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return f"US{self.number}"

    @classmethod
    def next_available_number(cls):
        """Starting point for new certificate ID generation"""
        try:
            return cls.objects.latest().number + 1
        except cls.DoesNotExist:
            return 1

    @classmethod
    def default_search_filters(cls):
        """Return default search as URL parameters"""
        q = QueryDict(mutable=True)
        q.setlist('status', cls.DEFAULT_SEARCH)
        return q.urlencode()
