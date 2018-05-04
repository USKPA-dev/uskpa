from django.contrib import admin
from django.urls import path, include

from django.views.generic import TemplateView

from kpc import views as kpc_views

urlpatterns = [
    path('accounts/', include('accounts.urls'), name='accounts'),
    path('about-us/', TemplateView.as_view(template_name='about.html'), name='about'),
    path('become-a-licensee/', TemplateView.as_view(template_name='join.html'), name='join'),
    path('register-certificate/', kpc_views.CertificateRegisterView.as_view(), name='cert-register'),
    path('certificates/<int:pk>/void', kpc_views.CertificateVoidView.as_view(), name='void'),
    path('certificates/<int:pk>', kpc_views.CertificateView.as_view(), name='cert-details'),
    path('certificates/', kpc_views.CertificateListView.as_view(), name='certificates'),
    path('certificates/export', kpc_views.ExportView.as_view(), name='export'),
    path('certificates-data/', kpc_views.CertificateJson.as_view(), name='certificate-data'),
    path('licensee-contacts/', kpc_views.licensee_contacts, name='licensee-contacts'),
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]
