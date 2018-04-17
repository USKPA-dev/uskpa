from model_mommy import mommy


# setup model_mommy for django-localflavor
def _gen_zipcode():
    return "00000-0000"


def _gen_state():
    return 'NY'


mommy.generators.add('localflavor.us.models.USZipCodeField', _gen_zipcode)
mommy.generators.add('localflavor.us.models.USStateField', _gen_state)
