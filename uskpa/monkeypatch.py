# Django 5.2 compatibility: utc_tzinfo_factory was removed
# Modern Django handles timezone settings automatically
# This monkeypatch is no longer needed

print("✅ Django 5.2+ timezone handling - no monkeypatch needed")
