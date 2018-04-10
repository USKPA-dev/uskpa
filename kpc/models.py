from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
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


class LabeledModel(models.Model):
    slug = models.SlugField()
    label = models.CharField(max_length=32)
    sort_order = models.IntegerField(help_text='Sort order override for select inputs',
                                     default=0)
    history = HistoricalRecords()

    class Meta:
        abstract = True

    def __str__(self):
        return self.label


class PaymentMethod(LabeledModel):
    """Valid certificate payment methods"""
    pass


class DeliveryStatus(LabeledModel):
    """Certificate delivery/processing statuses"""

    class Meta:
        verbose_name_plural = 'Delivery statuses'


class HSCode(models.Model):
    """
    The Harmonized Commodity Description and Coding System
    generally referred to as "Harmonized System" or simply "HS"
    is a multipurpose international product nomenclature developed
    by the World Customs Organization (WCO).
    """
    name = models.CharField(max_length=32)
    history = HistoricalRecords()

    class Meta:
        verbose_name = 'HS code'

    def __str__(self):
        return self.name


class Certificate(models.Model):

    # Fields on physical certificate
    number = models.PositiveIntegerField(help_text='USKPA Certificate ID number')
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
                                        blank=True, null=True, help_text="Value in U.S. $")
    exporter = models.CharField(blank=True, max_length=256)
    exporter_address = models.TextField(blank=True)
    number_of_parcels = models.PositiveIntegerField(blank=True, null=True)
    consignee = models.CharField(blank=True, max_length=256, help_text='Ultimate Consignee Name')
    consignee_address = models.TextField(blank=True, help_text='Ultimate Consignee Address')
    carat_weight = models.DecimalField(max_digits=20, decimal_places=10, blank=True, null=True)
    harmonized_code = models.ForeignKey('HSCode', blank=True, null=True, on_delete=models.PROTECT)

    # Non certificate fields
    assignor = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT)
    licensee = models.ForeignKey('Licensee', blank=True, null=True, on_delete=models.PROTECT)
    status = models.ForeignKey('DeliveryStatus', on_delete=models.PROTECT)
    last_modified = models.DateTimeField(default=timezone.now)
    date_of_sale = models.DateTimeField(blank=True, null=True, help_text='Date of sale to licensee')
    payment_method = models.ForeignKey('PaymentMethod', blank=True, null=True, on_delete=models.PROTECT)
    void = models.BooleanField(default=False, help_text="Certificate has been voided")
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
