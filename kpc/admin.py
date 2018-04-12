from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import Licensee


@admin.register(Licensee)
class LicenseeAdmin(SimpleHistoryAdmin, admin.ModelAdmin):
    list_display = ('name', 'address', 'primary_contact', 'city', 'state', 'zip_code', 'tax_id', )
