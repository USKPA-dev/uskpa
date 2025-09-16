from django.db.backends.postgresql.base import utc_tzinfo_factory
import django.db.backends.postgresql.base

def patched_utc_tzinfo_factory(offset):
    assert offset == 0, "database connection isn't set to UTC"
    print(">>> Django's utc_tzinfo_factory offset override engaged.")
    return utc_tzinfo_factory(offset)

django.db.backends.postgresql.base.utc_tzinfo_factory = patched_utc_tzinfo_factory

print("✅ Patched django.db.backends.postgresql.utils.utc_tzinfo_factory before DB connection")
