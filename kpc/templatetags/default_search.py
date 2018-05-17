from django import template
from kpc.models import Certificate

register = template.Library()


@register.simple_tag
def default_search(user):
    return '?' + Certificate.default_search_filters(user)
