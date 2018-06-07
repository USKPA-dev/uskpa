from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from simple_history.admin import SimpleHistoryAdmin
from solo.admin import SingletonModelAdmin

from accounts.models import Profile

from .models import (Certificate, CertificateConfig, HSCode, Licensee,
                     PortOfExport, VoidReason, KpcAddress, Receipt, EditRequest)


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
        fields = ('name', 'is_active', 'address', 'address2', 'city', 'state',
                  'zip_code', 'tax_id', 'contacts', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.fields['contacts'].initial = self.instance.contacts.all()


@admin.register(Licensee)
class LicenseeAdmin(SimpleHistoryAdmin):
    form = LicenseeAdminForm
    list_display = ('name', 'address', 'city', 'state', 'zip_code', 'tax_id', 'is_active')

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
            raise forms.ValidationError(
                "Date Issued cannot be set without Date Sold")
        if shipped and not issued:
            raise forms.ValidationError(
                "Date Shipped cannot be set without Date Issued")
        if delivered and not shipped:
            raise forms.ValidationError(
                "Date Delivered cannot be set without Date Shipped")

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
    change_form_template = "admin/cert-change.html"
    list_display = ('display_name', 'status',
                    'last_modified', 'licensee', 'assignor',)
    list_filter = ('status', 'licensee',)
    search_fields = ('number',)


@admin.register(PortOfExport)
class PortOfExportAdmin(SimpleHistoryAdmin):
    list_display = ('name', 'sort_order')


@admin.register(CertificateConfig)
class ConfigAdmin(SimpleHistoryAdmin, SingletonModelAdmin):
    change_form_template = "admin/cert-config-change.html"


class KpcAdmin(SimpleHistoryAdmin):
    list_display = ('value', 'sort_order')


@admin.register(Receipt)
class ReceiptAdmin(SimpleHistoryAdmin):
    list_display = ('number', 'licensee_name', 'contact', 'date_sold', 'certificates_sold')
    list_filter = ('date_sold', 'licensee_name', 'contact',)


@admin.register(EditRequest)
class EditRequestAdmin(admin.ModelAdmin):
    change_form_template = "admin/edit-request-change.html"
    list_display = ('id', 'certificate', 'date_requested', 'contact', 'status')
    list_filter = ('status', 'date_requested', 'contact')

    def get_readonly_fields(self, request, obj=None):
        """Set all fields to read-only"""
        return [f.name for f in self.model._meta.fields]


admin.site.register(HSCode, KpcAdmin)
admin.site.register(VoidReason, KpcAdmin)
admin.site.register(KpcAddress, admin.ModelAdmin)
