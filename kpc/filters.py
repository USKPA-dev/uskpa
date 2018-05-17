from django import forms
from django_filters import (DateFromToRangeFilter, FilterSet,
                            ModelChoiceFilter, MultipleChoiceFilter,
                            RangeFilter, CharFilter)
from django_filters.widgets import RangeWidget

from .models import Certificate


class RangeWidget(RangeWidget):
    template_name = 'filters/range_widget.html'


class CheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    option_template_name = 'uswds/radio_options.html'
    template_name = 'uswds/checkbox_input.html'


def licensees(request):
    return request.user.profile.get_licensees()


class CertificateFilter(FilterSet):
    DATE_ATTR = {'type': 'date', 'placeholder': 'mm/dd/yyyy'}

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
    licensee__name = ModelChoiceFilter(queryset=licensees)
    date_of_delivery = DateFromToRangeFilter(widget=RangeWidget(attrs=DATE_ATTR))
    date_of_shipment = DateFromToRangeFilter(widget=RangeWidget(attrs=DATE_ATTR))
    date_voided = DateFromToRangeFilter(widget=RangeWidget(attrs=DATE_ATTR))

    aes = CharFilter(lookup_expr='icontains')
    exporter = CharFilter(lookup_expr='icontains')
    exporter_address = CharFilter(lookup_expr='icontains')
    consignee = CharFilter(lookup_expr='icontains')
    consignee_address = CharFilter(lookup_expr='icontains')

    class Meta:
        model = Certificate

        default_fields = ['status', 'aes', 'date_of_issue']
        extra_fields = ['licensee__name', 'country_of_origin',
                        'harmonized_code', 'port_of_export',
                        'shipped_value',
                        'number_of_parcels', 'carat_weight',
                        'date_of_expiry', 'date_of_shipment', 'date_of_delivery',
                        'exporter', 'exporter_address',
                        'consignee', 'consignee_address',
                        'last_modified', 'date_of_sale', 'date_voided']

        fields = default_fields + extra_fields

    @property
    def default_fields(self):
        return [field for field in self.form if field.name in self.Meta.default_fields]

    @property
    def extra_fields(self):
        return [field for field in self.form if field.name in self.Meta.extra_fields]
