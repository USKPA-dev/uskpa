from django_filters import (DateFromToRangeFilter, FilterSet,
                            MultipleChoiceFilter, RangeFilter)

from django_filters.widgets import RangeWidget
from .models import Certificate
from django import forms


class RangeWidget(RangeWidget):
    template_name = 'filters/range_widget.html'


class CheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    option_template_name = 'uswds/radio_options.html'
    template_name = 'uswds/checkbox_input.html'


class CertificateFilter(FilterSet):
    DATE_ATTR = {'type': 'date'}

    status = MultipleChoiceFilter(
        choices=Certificate.STATUS_CHOICES,
        widget=CheckboxSelectMultiple(attrs={'class': 'usa-unstyled-list', 'legend': 'Certificate Status'}))
    last_modified = DateFromToRangeFilter(widget=RangeWidget(attrs=DATE_ATTR))
    date_of_sale = DateFromToRangeFilter(widget=RangeWidget(attrs=DATE_ATTR))
    shipped_value = RangeFilter(widget=RangeWidget())
    number_of_parcels = RangeFilter(widget=RangeWidget())
    carat_weight = RangeFilter(widget=RangeWidget())
    date_of_issue = DateFromToRangeFilter(widget=RangeWidget(attrs=DATE_ATTR))
    date_of_expiry = DateFromToRangeFilter(widget=RangeWidget(attrs=DATE_ATTR))

    class Meta:
        model = Certificate

        default_fields = ['status', 'last_modified', 'date_of_sale']
        extra_fields = ['country_of_origin', 'aes', 'harmonized_code',
                        'date_of_issue', 'date_of_expiry', 'shipped_value',
                        'number_of_parcels', 'carat_weight', 'exporter', 'exporter_address',
                        'consignee', 'consignee_address']

        fields = default_fields + extra_fields

    @property
    def default_fields(self):
        return [field for field in self.form if field.name in self.Meta.default_fields]

    @property
    def extra_fields(self):
        return [field for field in self.form if field.name in self.Meta.extra_fields]
