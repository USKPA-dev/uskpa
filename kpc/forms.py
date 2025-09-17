import datetime
import logging

from django import forms
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django_countries import Countries
from django_countries.fields import CountryField

from .models import (Certificate, CertificateConfig, EditRequest, KpcAddress,
                     Licensee, Receipt)

LOGGER = logging.getLogger(__name__)

User = get_user_model()

DATE_ATTRS = {'type': 'date', 'placeholder': 'mm/dd/yyyy'}


class USWDSRadioSelect(forms.RadioSelect):
    option_template_name = 'uswds/radio_options.html'


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name()


class AddressChoiceWidget(forms.widgets.Select):
    option_template_name = 'widgets/address_option.html'


from django_countries.data import COUNTRIES

class KPCountries(Countries):

    def __init__(self, *args, **kwargs):
        # Add the special code if it's not already present
        if '**' not in COUNTRIES:
            COUNTRIES['**'] = 'Mixed Origin'
        self.only = self._get_countries()
        super().__init__(*args, **kwargs)

    def _get_countries(self):
        """Return list of selectable countries"""
        countries = CertificateConfig.get_solo().kp_countries
        return [country.code for country in countries] + ['**']


class EditRequestReviewForm(forms.ModelForm):
    approve = forms.BooleanField(required=False)
    reject = forms.BooleanField(required=False)

    class Meta:
        model = EditRequest
        fields = ()

    def _get_review(self):
        '''fetch review from incoming data'''
        approve = self.cleaned_data.get('approve')
        reject = self.cleaned_data.get('reject')
        return approve, reject

    def clean(self):
        if self.instance.status != EditRequest.PENDING:
            raise forms.ValidationError('This request has already been reviewed.')
        approve, reject = self._get_review()

        if not approve and not reject:
            raise forms.ValidationError('Request must be approved or rejected.')

        if approve and reject:
            raise forms.ValidationError('Request must be approved or rejected, not both.')

    def save(self, reviewer=None):
        """Set reviewed status and reviewer"""
        approve, _ = self._get_review()
        edit_request = self.instance
        edit_request.reviewed_by = reviewer
        edit_request.date_reviewed = datetime.datetime.now()
        if approve:
            edit_request.approve()
        else:
            edit_request.reject()
        edit_request.save()
        return edit_request


class BaseCertificateForm(forms.ModelForm):
    date_of_issue = forms.DateField(widget=forms.DateInput(attrs=DATE_ATTRS))

    COUNTRY_MISSING = """Address must contain a
                         participating KP country name,
                         spelled identically to those listed in
                         the Country of Origin field on this form."""

    class Meta:
        model = Certificate
        fields = ('aes', 'country_of_origin', 'shipped_value', 'exporter', 'exporter_address',
                  'number_of_parcels', 'consignee', 'consignee_address', 'carat_weight', 'harmonized_code',
                  'date_of_issue', 'date_of_expiry', 'attested', 'port_of_export')

    def __init__(self, *args, **kwargs):
        """
        All fields are required
        Populate address books
        Set selectable countries
        """
        super().__init__(*args, **kwargs)
        self.expiry_days = Certificate.get_expiry_days()
        self.date_expiry_invalid = f'Date of Expiry must be {self.expiry_days} days after Date of Issue (expected %s)'
        self.fields['date_of_expiry'].label = f"Date of Expiry ({self.expiry_days} days from date issued)"
        self.fields['country_of_origin'] = CountryField(countries=KPCountries).formfield()
        addresses = self.instance.licensee.addresses.all() if self.instance.licensee else None
        self.fields['addresses'] = forms.ModelChoiceField(required=False, queryset=addresses)
        for field in self.fields:
            if field != 'addresses':
                self.fields[field].required = True

    def find_kp_country(self, address):
        """
        Check for a KP country name in address
        """
        countries = [country.name.lower() for country in KPCountries()]
        address = address.lower()
        if not any(country in address for country in countries):
            raise forms.ValidationError(self.COUNTRY_MISSING)

    def clean_exporter_address(self):
        address = self.cleaned_data.get('exporter_address')
        self.find_kp_country(address)
        return address

    def clean_consignee_address(self):
        address = self.cleaned_data.get('consignee_address')
        self.find_kp_country(address)
        return address

    def clean(self):
        date_of_issue = self.cleaned_data.get('date_of_issue')
        date_of_expiry = self.cleaned_data.get('date_of_expiry')

        # Date of expiry must be CertificateConfig.expiry_days after date of issue
        if date_of_issue and date_of_expiry:
            delta = date_of_expiry - date_of_issue
            expected_date = date_of_issue + datetime.timedelta(days=self.expiry_days)
            if delta.days != self.expiry_days:
                self.add_error('date_of_expiry', self.date_expiry_invalid % expected_date.strftime('%m/%d/%Y'))


class LicenseeCertificateForm(BaseCertificateForm):
    date_of_expiry = forms.DateField(widget=forms.DateInput(attrs={'readonly': 'readonly',
                                                                   'placeholder': 'Auto-filled from Date of Issue'}))

    SUCCESS_MSG = "Thank you! Your certificate has been successfully issued."

    def __init__(self, *args, **kwargs):
        """prepopulate licensee field and disable if not editable"""
        self.editable = kwargs.pop('editable', True)
        super().__init__(*args, **kwargs)
        if self.instance.licensee:
            self.initial.update({'exporter': self.instance.licensee.name,
                                 'exporter_address': self.instance.licensee.address_text})
        for field in self.fields:
            if not self.editable:
                self.fields[field].disabled = True

    def save(self, commit=True):
        """Set status to PREPARED"""
        if commit:
            self.instance.status = Certificate.PREPARED
            self.instance.save()
        return self.instance


class EditRequestForm(BaseCertificateForm):
    date_of_expiry = forms.DateField(widget=forms.DateInput(attrs=DATE_ATTRS))

    def __init__(self, *args, **kwargs):
        """Remove attestation field when requesting a certificate edit"""
        super().__init__(*args, **kwargs)
        self.fields.pop('attested')

    def save(self, commit=True, contact=None):
        """Save changed fields to an EditRequest instance"""
        if self.has_changed():
            edit_request = EditRequest(
                certificate=self.instance, contact=contact)
            for field in self.changed_data:
                setattr(edit_request, field, self.cleaned_data.get(field))
            edit_request.save()
        return edit_request


class CertificateRegisterForm(forms.Form):
    LIST = 'list'
    SEQUENTIAL = 'sequential'

    REGISTRATION_METHODS = ((SEQUENTIAL, 'Sequential'), (LIST, 'List'))

    licensee = forms.ModelChoiceField(
        queryset=Licensee.objects.filter(is_active=True))
    contact = UserModelChoiceField(
        queryset=User.objects.filter(is_active=True))
    date_of_sale = forms.DateField(
        initial=datetime.date.today, widget=forms.DateInput(attrs=DATE_ATTRS))
    registration_method = forms.ChoiceField(choices=REGISTRATION_METHODS,
                                            widget=USWDSRadioSelect(
                                                attrs={'class': 'usa-unstyled-list'}),
                                            initial=SEQUENTIAL)
    cert_from = forms.IntegerField(min_value=0, required=False, label='From')
    cert_to = forms.IntegerField(min_value=1, required=False, label='To')
    cert_list = forms.CharField(required=False, label='Certificate ID list',
                                validators=[
                                    RegexValidator(regex=r'^(\d+(,\d+)*)?$',
                                                   message='Certificate list must be a comma delimited list of numeric IDs, without spaces.'
                                                   )
                                ])
    payment_method = forms.ChoiceField(
        choices=Certificate.PAYMENT_METHOD_CHOICES)
    payment_amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.price = Certificate.get_price()
        self.fields[
            'payment_amount'].label = f'Payment amount (Certificate price: ${self.price})'

        data = kwargs.get('data', None)
        if data:
            licensee = data.get('licensee', None)
            contact = data.get('contact', None)
            if licensee:
                self.fields['contact'].queryset = \
                    User.objects.filter(is_active=True,
                                        profile__licensees__in=[licensee])
            if contact:
                self.fields['contact'].initial = contact
        else:
            self.fields['contact'].choices = [
                ('', self.fields['contact'].empty_label)]
        self.fields['cert_from'].initial = Certificate.next_available_number()

    def clean(self):
        """Validations requiring cross-field checks"""
        cleaned_data = super().clean()
        licensee = cleaned_data.get("licensee")
        contact = cleaned_data.get("contact")
        cert_from = cleaned_data.get("cert_from")
        cert_to = cleaned_data.get("cert_to")
        cert_list = cleaned_data.get("cert_list")
        payment_amount = cleaned_data.get("payment_amount")
        self.method = cleaned_data.get('registration_method')

        if licensee and contact:
            if not contact.profile.licensees.filter(id=licensee.id).exists():
                raise forms.ValidationError(
                    "Contact is not associated with selected Licensee"
                )

        if self.method == self.LIST and not cert_list:
            self.add_error('cert_list', 'Valid list of ID values required.')
            raise forms.ValidationError(
                "A valid certificate list must be provided when List method is selected.")

        if self.method == self.SEQUENTIAL and (not cert_from or not cert_to):
            raise forms.ValidationError(
                "Certificate To and From must be provided when Sequential method is selected.")

        if cert_from and cert_to:
            if cert_from > cert_to:
                self.add_error('cert_from', 'Value must be less than "To"')
                self.add_error(
                    'cert_to', 'Value must be greater than or equal to "From"')
                raise forms.ValidationError(
                    "Certificate 'To' value must be greater than or equal to 'From' value.")

        requested_certs = self.get_cert_list()
        """duplicate certs requested"""
        if len(requested_certs) != len(set(requested_certs)):
            raise forms.ValidationError(
                f"At least two requested certificates were requested with the same ID value, duplicate certificate IDs are not allowed.")

        """payment amount matches expected value"""
        requested_cert_count = len(requested_certs)
        expected_payment = requested_cert_count * self.price
        if payment_amount != expected_payment:
            raise forms.ValidationError(
                f"A payment of ${expected_payment} is required. ({requested_cert_count} requested certificates @ ${self.price} per certificate.)")

        # Check for existence of requested certificates
        existing = Certificate.objects.filter(
            number__in=requested_certs).exists()
        if existing:
            raise forms.ValidationError(
                f"""At least one of the requested certificates already exists in the database.
                    The next available certificate number is: {Certificate.next_available_number()}""")

    def get_cert_list(self):
        """return list of certificates to generate"""
        certs = []
        cert_list = self.cleaned_data.get('cert_list')
        start = self.cleaned_data.get('cert_from')
        end = self.cleaned_data.get('cert_to')
        if self.method == self.SEQUENTIAL and start and end:
            certs = [i for i in range(start, end+1)]
        elif self.method == self.LIST and cert_list:
            certs = [int(cert_number) for cert_number in cert_list.split(',')]
        return certs

    def save(self, commit=False):
        """Generate receipt for this transaction"""
        receipt = Receipt.from_registration_form(self)
        receipt.save()
        return receipt


class StatusUpdateForm(forms.ModelForm):
    date = forms.DateField(required=True)
    next_status = forms.IntegerField(required=True)

    UNEXPECTED_STATUS = 'Unable to update status, please reload the page and try again.'
    SHIPPED_DATE = "The Shipped date must be on or after the certificate's date of issue (%s)."
    DELIVERY_DATE = "The Delivered date must be on or after the certificate's date of shipment (%s)."
    NOT_AVAILABLE = "This certificate has already been issued."
    SUCCESS_MSG = 'Certificate status has been successfully updated.'

    def __init__(self, *args, **kwargs):
        self.editable = kwargs.pop('editable', False)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Certificate
        fields = ("date", 'next_status')

    def clean(self):
        """Dates must be ordered"""
        if 'attested' in self.data.keys():
            # Certificate issue form was submitted
            # We're expecting only status changes
            # Likely certificate was issued while form was being completed.
            raise forms.ValidationError(self.NOT_AVAILABLE)

        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        new_status = cleaned_data.get('next_status')

        if new_status != self.instance.next_status_value:
            raise forms.ValidationError(self.UNEXPECTED_STATUS)

        if date and new_status == Certificate.SHIPPED:
            if date < self.instance.date_of_issue:
                raise forms.ValidationError(
                    self.SHIPPED_DATE % self.instance.date_of_issue)

        if date and new_status == Certificate.DELIVERED:
            if date < self.instance.date_of_shipment:
                raise forms.ValidationError(
                    self.DELIVERY_DATE % self.instance.date_of_shipment)

    def save(self):
        """Set our new status and associated date"""
        date = self.cleaned_data['date']
        new_status = self.cleaned_data['next_status']
        self.instance.status = new_status

        if new_status == Certificate.SHIPPED:
            self.instance.date_of_shipment = date
        if new_status == Certificate.DELIVERED:
            self.instance.date_of_delivery = date

        self.instance.save()
        LOGGER.info(
            f'{self.instance} status updated to: {self.instance.get_status_display()}')
        return self.instance


class VoidForm(forms.ModelForm):
    OTHER_CHOICE = 'Other'
    void = forms.BooleanField(help_text="I wish to void this certificate.")
    reason = forms.ChoiceField(choices=[])
    notes = forms.CharField(widget=forms.Textarea(), required=False)

    REASON_REQUIRED = "Please provide a reason for this action."

    class Meta:
        model = Certificate
        fields = ("void", "notes")

    def __init__(self, *args, **kwargs):
        """Set void reason choices"""
        choices = [('', '---------')]
        choices += [(reason.value, reason.value)
                    for reason in Certificate.get_void_reasons()]
        choices += [('Other', 'Other')]
        super().__init__(*args, **kwargs)
        self.fields['reason'].choices = choices

    def clean(self):
        reason = self.cleaned_data.get('reason')
        notes = self.cleaned_data.get('notes')

        if reason == self.OTHER_CHOICE and not notes:
            self.add_error('notes', self.REASON_REQUIRED)

    def save(self):
        """Set status to void"""
        cert = self.instance
        cert.status = Certificate.VOID
        cert.void = True
        cert.notes = self.cleaned_data['notes'] or self.cleaned_data['reason']
        cert.date_voided = datetime.date.today()
        cert.save()
        LOGGER.info(f'{self.instance} voided')
        return cert


class KpcAddressForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        """
        Limit country field
        """
        super().__init__(*args, **kwargs)
        self.fields['country'] = CountryField(countries=KPCountries).formfield(
            help_text='Appended to address when pre-populating a Certificate address field')

    class Meta:
        model = KpcAddress
        fields = ('name', 'address', 'country')
