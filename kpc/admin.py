from django.contrib import admin
from .models import Licensee


@admin.register(Licensee)
class LicenseeAdmin(admin.ModelAdmin):
    pass
