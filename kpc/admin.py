from django import forms
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from simple_history.admin import SimpleHistoryAdmin

from accounts.models import Profile

from .models import Licensee


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
class LicenseeAdmin(SimpleHistoryAdmin, admin.ModelAdmin):
    form = LicenseeAdminForm
    list_display = ('name', 'address', 'city', 'state', 'zip_code', 'tax_id', )

    def save_related(self, request, form, formsets, change):
        """
        Save licensee contacts
        """
        licensee = form.save(commit=False)
        licensee.contacts.set(form.cleaned_data['contacts'])
        super().save_related(request, form, formsets, change)
