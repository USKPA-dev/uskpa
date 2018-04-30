from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.http import QueryDict
from django_countries.fields import CountryField
from localflavor.us.models import USStateField, USZipCodeField
from simple_history.models import HistoricalRecords
from django.urls import reverse


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

    def get_absolute_url(self):
        return reverse('licensee', args=[self.id])

    def user_can_access(self, user):
        return user.is_superuser or user.profile.licensees.filter(id=self.id).exists()


class Certificate(models.Model):
    ASSIGNED = 0
    PREPARED = 1
    INTRANSIT = 2
    DELIVERED = 3
    VOID = 4

    DEFAULT_SEARCH = [ASSIGNED, PREPARED, INTRANSIT]
    MODIFIABLE_STATUSES = [PREPARED, INTRANSIT]

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

    VOID_REASONS = ['Printing Error', 'Typographical error', 'No longer needed', 'Other']

    # Fields on physical certificate
    number = models.PositiveIntegerField(help_text='USKPA Certificate ID number', unique=True)
    aes = models.CharField(max_length=15,
                           blank=True,
                           help_text='AES Confirmation Number (ITN)',
                           verbose_name='AES',
                           validators=[
                                RegexValidator(regex='X\d{14}',
                                               message='AES Confirmation (ITN) format is 14 digits prepended by X: X##############'
                                               )
                                    ]
                           )
    country_of_origin = CountryField(blank=True, verbose_name='Country of Origin')
    date_of_issue = models.DateField(blank=True, null=True, help_text='Date of Issue')
    date_of_expiry = models.DateField(blank=True, null=True, help_text='Date of Expiry')
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
    date_of_sale = models.DateField(blank=True, null=True, help_text='Date of sale to licensee')
    payment_method = models.CharField(choices=PAYMENT_METHOD_CHOICES, max_length=5,
                                      blank=True)
    void = models.BooleanField(default=False, help_text="Certificate has been voided?")
    notes = models.TextField(blank=True)

    attested = models.BooleanField(default=False, help_text="""I have completed the necessary
                                                                application pertaining to this shipment,
                                                                including the warranty that the diamonds
                                                                being shipped were not traded to fund conflict.""")
    date_of_shipment = models.DateField(blank=True, null=True, help_text='Date certificate was marked IN TRANSIT')
    date_of_delivery = models.DateField(blank=True, null=True, help_text='Date certificate was marked DELIVERED')
    date_voided = models.DateField(blank=True, null=True, help_text="Date on which this certificate was voided")
    history = HistoricalRecords()

    class Meta:
        get_latest_by = ('number', )

    def __str__(self):
        return self.display_name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('cert-details', args=[self.id])

    def get_anchor_tag(self):
        """Link to this object"""
        return f"<a href={self.get_absolute_url()}>{self.display_name}</a>"

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

    @property
    def licensee_editable(self):
        return self.status == self.ASSIGNED

    @property
    def status_can_be_updated(self):
        """Certificate may be modified by users?"""
        return self.status in self.MODIFIABLE_STATUSES

    @property
    def next_status_label(self):
        """Return label of next status"""
        if self.status in self.MODIFIABLE_STATUSES:
            return dict(self.STATUS_CHOICES)[self.status+1]

    @property
    def next_status_value(self):
        """Return value of next status"""
        if self.status in self.MODIFIABLE_STATUSES:
            return self.status+1

    def user_can_access(self, user):
        """True if user can access this certificate"""
        return user.profile.certificates().filter(id=self.id).exists()

    @classmethod
    def get_label_for_status(cls, status):
        return dict(cls.STATUS_CHOICES).get(status)
