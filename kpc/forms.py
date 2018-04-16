import datetime

from django import forms
from django.contrib.auth import get_user_model

from .models import Certificate, Licensee, PaymentMethod

User = get_user_model()


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.get_full_name()


class CertificateRegisterForm(forms.Form):
    REGISTRATION_METHODS = (('list', 'list'), ('sequential', 'sequential'))

    licensee = forms.ModelChoiceField(queryset=Licensee.objects.all())
    contact = UserModelChoiceField(queryset=User.objects, empty_label='Select a licensee')
    date_of_issue = forms.DateTimeField(initial=datetime.date.today)
    registration_method = forms.ChoiceField(choices=REGISTRATION_METHODS)
    cert_from = forms.IntegerField(min_value=0, required=False, label='From')
    cert_to = forms.IntegerField(min_value=1, required=False, label='To')
    cert_list = forms.CharField(required=False, label='Certificate ID list')
    payment_method = forms.ModelChoiceField(queryset=PaymentMethod.objects.all())
    payment_amount = forms.DecimalField(max_digits=10, decimal_places=2)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        data = kwargs.get('data', None)
        if data:
            licensee = data.get('licensee', None)
            contact = data.get('contact', None)
            if licensee:
                self.fields['contact'].queryset = User.objects.filter(profile__licensees__in=[licensee])
            if contact:
                self.fields['contact'].initial = contact
        else:
            self.fields['contact'].choices = [('', 'Select a licensee')]
        self.fields['cert_from'].initial = Certificate.objects.next_available()

    def clean(self):
        """Validations requiring cross-field checks"""
        cleaned_data = super().clean()
        licensee = cleaned_data.get("licensee")
        contact = cleaned_data.get("contact")
        cert_from = cleaned_data.get("cert_from")
        cert_to = cleaned_data.get("cert_to")
        cert_list = cleaned_data.get("cert_list")
        method = cleaned_data.get('registration_method')

        if licensee and contact:
            if not contact.profile.licensees.filter(id=licensee.id).exists():
                raise forms.ValidationError(
                    "Contact is not associated with selected Licensee"
                )

        if method == 'list' and not cert_list:
            self.add_error('cert_list', 'List of ID values required.')
            raise forms.ValidationError("Certificate List must be provided when List method is selected.")

        if method == 'sequential' and (not cert_from or not cert_to):
            raise forms.ValidationError("Certificate To and From must be provided when Sequential method is selected.")

        if cert_from and cert_to:
            if cert_from > cert_to:
                self.add_error('cert_from', 'Value must be less than "To"')
                self.add_error('cert_to', 'Value must be greater than or equal to "From"')
                raise forms.ValidationError("Certificate 'To' value must be greater than or equal to 'From' value.")

        # TODO more validation to be done here.
        # Check for requested Cert Number conflicts before attempting creation
