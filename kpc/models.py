from django.db import models
from django.core.validators import RegexValidator
from localflavor.us.models import USZipCodeField, USStateField
from simple_history.models import HistoricalRecords


class Licensee(models.Model):
    """
    An entity involved in the export/import of rough diamonds
    within the United States
    """
    name = models.CharField(max_length=256)
    primary_contact = models.CharField(max_length=32)
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
