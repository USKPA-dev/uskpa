from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from simple_history.admin import SimpleHistoryAdmin

from accounts.models import Profile

from .models import Certificate, Licensee, HSCode

admin.site.register(HSCode)


class LicenseeAdminForm(forms.ModelForm):
    contacts = forms.ModelMultipleChoiceField(
        queryset=Profile.objects.all(),
        required=False,
        widget=FilteredSelectMultiple(
            verbose_name='Contacts',
            is_stacked=False
        )
    )

    class Meta:
        model = Licensee
        fields = ('name', 'address', 'address2', 'city', 'state',
                  'zip_code', 'tax_id', 'contacts', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['contacts'].initial = self.instance.contacts.all()


@admin.register(Licensee)
class LicenseeAdmin(SimpleHistoryAdmin):
    form = LicenseeAdminForm
    list_display = ('name', 'address', 'city', 'state', 'zip_code', 'tax_id', )

    def save_related(self, request, form, formsets, change):
        """
        Save licensee contacts
        """
        licensee = form.save(commit=False)
        licensee.contacts.set(form.cleaned_data['contacts'])
        super().save_related(request, form, formsets, change)


class CertificateAdminForm(forms.ModelForm):
    """Enforce date consistency"""
    class Meta:
        model = Certificate
        fields = ("__all__")

    def clean(self):
        cleaned_data = super().clean()

        sold = cleaned_data.get('date_of_sale')
        issued = cleaned_data.get('date_of_issue')
        shipped = cleaned_data.get('date_of_shipment')
        delivered = cleaned_data.get('date_of_delivery')

        if issued and not sold:
            raise forms.ValidationError("Date Issued cannot be set without Date Sold")
        if shipped and not issued:
            raise forms.ValidationError("Date Shipped cannot be set without Date Issued")
        if delivered and not shipped:
            raise forms.ValidationError("Date Delivered cannot be set without Date Shipped")

        if sold and issued:
            if issued < sold:
                raise forms.ValidationError(
                    'Date issued can not pre-date Date Sold')
            if shipped:
                if shipped < issued:
                    raise forms.ValidationError(
                        'Date shipped can not pre-date Date Issued')
                if delivered and delivered < shipped:
                        raise forms.ValidationError(
                            'Date delivered can not pre-date Date Shipped')


@admin.register(Certificate)
class CertificateAdmin(SimpleHistoryAdmin):
    form = CertificateAdminForm
    list_display = ('display_name', 'status',
                    'last_modified', 'licensee', 'assignor',)
    list_filter = ('status', 'licensee',)
    search_fields = ('number',)
