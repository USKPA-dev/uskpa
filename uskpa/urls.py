from django.apps import apps
from django.contrib import admin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView

from kpc import views as kpc_views

kpc_config = apps.get_app_config('kpc')

urlpatterns = [
    path('accounts/', include('accounts.urls'), name='accounts'),
    path('become-a-licensee/', TemplateView.as_view(template_name='join.html'), name='join'),
    path('register-certificate/', kpc_views.CertificateRegisterView.as_view(), name='cert-register'),
    path('certificates/<int:number>/confirm', kpc_views.CertificateConfirmView.as_view(), name='confirm'),
    path('certificates/<int:number>/void', kpc_views.CertificateVoidView.as_view(), name='void'),
    path('certificates/<int:number>', kpc_views.CertificateView.as_view(), name='cert-details'),
    path('certificates/', kpc_views.CertificateListView.as_view(), name='certificates'),
    path('certificates/export', kpc_views.ExportView.as_view(), name='export'),
    path('certificates-data/', kpc_views.CertificateJson.as_view(), name='certificate-data'),
    path('licensee/<int:pk>', kpc_views.LicenseeDetailView.as_view(), name='licensee'),
    path('licensee/<int:pk>/new_addressee', kpc_views.KpcAddressCreate.as_view(), name='new-addressee'),
    path('addressee/<int:pk>', kpc_views.KpcAddressUpdate.as_view(), name='addressee'),
    path('addressee/<int:pk>/delete', kpc_views.KpcAddressDelete.as_view(), name='addressee-delete'),
    path('licensee-contacts/', kpc_views.licensee_contacts, name='licensee-contacts'),
    path('receipt/<int:pk>', kpc_views.ReceiptView.as_view(), name='receipt'),
    path('admin/', admin.site.urls),
    path('favicon.ico',
         RedirectView.as_view(url=staticfiles_storage.url('assets/icons/favicon.ico')),
         name="favicon"
         ),
    path('', TemplateView.as_view(template_name='home.html',
                                  extra_context={'config': kpc_config}), name='home'),
]
