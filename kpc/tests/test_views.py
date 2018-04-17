import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from model_mommy import mommy

from kpc.models import Certificate
from kpc.views import CertificateRegisterView, licensee_contacts


class LicenseeContactsTests(TestCase):

    def setUp(self):
        self.user = mommy.make(settings.AUTH_USER_MODEL)
        self.factory = RequestFactory()
        user_ct = ContentType.objects.get(app_label='accounts', model='profile')
        self.p, _ = Permission.objects.get_or_create(content_type=user_ct, codename='can_get_licensee_contacts', name="can_get_licensee_contacts")
        self.request = self.factory.get('')
        self.request.user = self.user

    def test_not_accessible_without_perm(self):
        """Cannot access without perm"""
        with self.assertRaises(PermissionDenied):
            licensee_contacts(self.request)

    def test_only_get_allowed(self):
        """
        405 response if request is not a GET
        """
        self.user.user_permissions.add(self.p)
        for method in ['post', 'put', 'delete', 'head', 'options', 'trace']:
            request = getattr(self.factory, method)('')
            request.user = self.user
            response = licensee_contacts(request)
            self.assertEqual(response.status_code, 405)

    def test_returns_empty_list_if_no_licensee(self):
        """Return empty json list if no licensee provided"""
        licensee = mommy.make('kpc.Licensee')
        self.user.user_permissions.add(self.p)
        self.user.profile.licensees.add(licensee)
        response = licensee_contacts(self.request)
        self.assertEqual(response.content, b'[]')

    def test_returns_user_list_if_licensee(self):
        """
        Return json list of users associated
        to provided licensee
        """
        licensee = mommy.make('kpc.Licensee')
        self.user.user_permissions.add(self.p)
        self.user.profile.licensees.add(licensee)
        request = self.factory.get('', {'licensee': licensee.id})
        request.user = self.user
        response = licensee_contacts(request)
        self.assertEqual(json.loads(response.content),
                         [{'id': self.user.id, 'name': self.user.profile.get_user_display_name()}])


class CertificateRegisterViewTests(TestCase):

    def setUp(self):
        self.licensee = mommy.make('Licensee')
        self.admin_user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=True)
        self.user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        self.user.profile.licensees.add(self.licensee)

        payment = mommy.make('PaymentMethod')
        # Valid registration form input
        self.sequential_kwargs = {'registration_method': 'sequential',  'cert_from': 1, 'cert_to': 5}
        self.list_kwargs = {'registration_method': 'list', 'cert_list': 'US201, US123456'}
        self.form_kwargs = {'licensee': self.licensee.id, 'contact': self.user.id,
                            'date_of_issue': '01/01/2018',
                            'payment_method': payment.id, 'payment_amount': 1
                            }
        self.factory = RequestFactory()

    def test_must_be_logged_in(self):
        """redirect to login if not authenticated"""
        request = self.factory.post('')
        request.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            CertificateRegisterView.as_view()(request)

    def test_user_cannot_access(self):
        """Non-superusers cannot access"""
        request = self.factory.post('')
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            CertificateRegisterView.as_view()(request)

    def test_superuser_can_access(self):
        """Superusers can access"""
        request = self.factory.post('')
        request.user = self.admin_user
        response = CertificateRegisterView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_sequential_generation(self):
        """
        Generate certs numbered CERT_FROM to CERT_TO inclusive
        provide user with message reflecting number of certs generated
        """
        client = Client()
        client.force_login(self.admin_user)
        mommy.make('DeliveryStatus', slug='assigned')
        self.form_kwargs.update(self.sequential_kwargs)

        response = client.post(reverse('cert-register'), self.form_kwargs, follow=True)
        self.assertEqual(Certificate.objects.count(), 5)

        message = list(response.context['messages']).pop()
        self.assertEqual(message.message, 'Generated 5 new certificates.')

    def test_list_generation(self):
        """
        Generate certs parsed from CERT_LIST
        provide user with message reflecting number of certs generated
        """
        client = Client()
        client.force_login(self.admin_user)
        mommy.make('DeliveryStatus', slug='assigned')
        self.form_kwargs.update(self.list_kwargs)

        response = client.post(reverse('cert-register'), self.form_kwargs, follow=True)

        self.assertEqual(Certificate.objects.count(), 2)

        message = list(response.context['messages']).pop()
        self.assertEqual(message.message, 'Generated 2 new certificates.')
