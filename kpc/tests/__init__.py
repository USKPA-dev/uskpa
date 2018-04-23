from model_mommy import mommy

# setup model_mommy for django-localflavor
mommy.generators.add('localflavor.us.models.USZipCodeField', lambda: "00000-0000")
mommy.generators.add('localflavor.us.models.USStateField', lambda: "NY")
