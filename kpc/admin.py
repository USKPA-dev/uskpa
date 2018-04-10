from django.contrib import admin
from .models import Licensee


@admin.register(Licensee)
class LicenseeAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'primary_contact', 'city', 'state', 'zip_code', 'tax_id', )
