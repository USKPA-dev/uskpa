from django.db.backends import postgresql
import warnings

def patched_utc_tzinfo_factory(offset):
    if offset != 0:
        warnings.warn(f"[MonkeyPatch] Non-zero offset detected: {offset} — forcing UTC anyway.")
    return None  # Return UTC-compatible tzinfo (None is okay)

# Apply the patch
postgresql.utils.utc_tzinfo_factory = patched_utc_tzinfo_factory

print("✅ Patched django.db.backends.postgresql.utils.utc_tzinfo_factory before DB connection")