import datetime
import json

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from model_mommy import mommy

from kpc.forms import LicenseeCertificateForm, StatusUpdateForm
from kpc.models import Certificate
from kpc.tests import CERT_FORM_KWARGS, load_groups
from kpc.views import (CertificateJson, CertificateRegisterView,
                       CertificateView, CertificateVoidView, licensee_contacts)


def _get_expiry_date(date_of_issue):
    """determine expiry date"""
    issued = datetime.datetime.strptime(date_of_issue, "%m/%d/%Y").date()
    date_of_expiry = issued + \
        datetime.timedelta(days=Certificate.get_expiry_days())
    return date_of_expiry.strftime('%m/%d/%Y')


class CertTestCase(TestCase):

    def get_form_kwargs(self):
        base_kwargs = CERT_FORM_KWARGS.copy()
        base_kwargs['harmonized_code'] = mommy.make('HScode').id
        base_kwargs['date_of_expiry'] = _get_expiry_date(
            base_kwargs['date_of_issue'])
        return base_kwargs

    def setUp(self):
        self.user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=True)
        self.form_kwargs = self.get_form_kwargs()
        self.c = Client()
        self.c.force_login(self.user)


class LicenseeContactsTests(TestCase):

    def setUp(self):
        self.user = mommy.make(settings.AUTH_USER_MODEL)
        self.factory = RequestFactory()
        user_ct = ContentType.objects.get(
            app_label='accounts', model='profile')
        self.p, _ = Permission.objects.get_or_create(
            content_type=user_ct, codename='can_get_licensee_contacts', name="can_get_licensee_contacts")
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
        self.admin_user = mommy.make(
            settings.AUTH_USER_MODEL, is_superuser=True)
        self.user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        self.user.profile.licensees.add(self.licensee)

        # Valid registration form input
        self.sequential_kwargs = {
            'registration_method': 'sequential',  'cert_from': 1, 'cert_to': 5}
        self.list_kwargs = {'registration_method': 'list', 'payment_amount': 40,
                            'cert_list': 'US201, US123456'}
        self.form_kwargs = {'licensee': self.licensee.id, 'contact': self.user.id,
                            'date_of_sale': '01/01/2018',
                            'payment_method': 'cash', 'payment_amount': 100
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
        self.form_kwargs.update(self.sequential_kwargs)

        response = client.post(reverse('cert-register'),
                               self.form_kwargs, follow=True)
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
        self.form_kwargs.update(self.list_kwargs)

        response = client.post(reverse('cert-register'),
                               self.form_kwargs, follow=True)

        self.assertEqual(Certificate.objects.count(), 2)

        message = list(response.context['messages']).pop()
        self.assertEqual(message.message, 'Generated 2 new certificates.')


class CertificateViewTests(CertTestCase):

    def test_status_form_when_not_editable(self):
        """
        status form is used when certificate is not editable
        by licensees
        """
        cert = mommy.make(Certificate, status=Certificate.INTRANSIT)
        form = CertificateView(object=cert).get_form_class()
        self.assertIs(form, StatusUpdateForm)

    def test_cert_form_when_editable(self):
        """Licensee form is used when certificate is  editable"""
        cert = mommy.make(Certificate, status=Certificate.ASSIGNED)
        form = CertificateView(object=cert).get_form_class()
        self.assertIs(form, LicenseeCertificateForm)

    def test_editable_form_rendered_if_assigned(self):
        cert = mommy.make(Certificate, status=Certificate.ASSIGNED)
        """User gets an editable form if certificate is editable"""
        response = self.c.get(cert.get_absolute_url())
        self.assertTemplateUsed(response, 'certificate/details-edit.html')

    def test_non_editable_form_rendered_if_assigned(self):
        """User gets a non-editable form if certificate is editable"""
        cert = mommy.make(Certificate, status=Certificate.VOID)
        response = self.c.get(cert.get_absolute_url())
        self.assertTemplateUsed(response, 'certificate/details.html')

    def test_form_invalid_if_cert_is_not_assigned(self):
        """Users can't use this form if certificate is not ASSIGNED"""
        cert = mommy.make(Certificate, status=Certificate.VOID)
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        self.assertContains(response, StatusUpdateForm.NOT_AVAILABLE)

    def test_form_invalid_if_not_all_fields_provided(self):
        """Form invalid without all fields"""
        cert = mommy.make(Certificate, status=Certificate.ASSIGNED)
        self.form_kwargs.pop('consignee')
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        cert.refresh_from_db()
        self.assertEqual(cert.status, Certificate.ASSIGNED)
        self.assertTemplateUsed(response, 'certificate/details-edit.html')
        self.assertContains(response, 'required')

    def test_next_status_input_rendered_when_moddable(self):
        """Button to advance status is rendered if status can be changed"""
        cert = mommy.make(Certificate, status=Certificate.INTRANSIT)
        response = self.c.get(cert.get_absolute_url())
        self.assertContains(
            response, f'Set status to: {cert.next_status_label}')

    def test_next_status_input_not_rendered_when_unmoddable(self):
        """Button to advance status is NOT rendered if status cannot be changed"""
        cert = mommy.make(Certificate, status=Certificate.VOID)
        response = self.c.get(cert.get_absolute_url())
        self.assertNotContains(response, 'Set status')

    def test_form_valid_if_cert_is_assigned(self):
        """Cert unchanged and confirmation template displayed w/ valid form"""
        cert = mommy.make(Certificate, status=Certificate.ASSIGNED)
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        cert.refresh_from_db()
        self.assertEqual(cert.status, Certificate.ASSIGNED)
        self.assertTemplateUsed(response, 'certificate/preview.html')

    def test_fields_rendered_for_review(self):
        """Fields rendered for review template"""
        cert = mommy.make(Certificate, status=Certificate.ASSIGNED)
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        for field in self.form_kwargs.keys():
            self.assertContains(response, field)

    def test_pdf_preview_data_in_context(self):
        """Data for PDF preview is included in context"""
        cert = mommy.make(Certificate, status=Certificate.ASSIGNED)
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        self.assertTrue('b64_pdf' in response.context)

    def test_edit_form_for_changes_w_get_params(self):
        """When get params provided, render prepopulated form"""
        cert = mommy.make(Certificate, status=Certificate.ASSIGNED)
        response = self.c.get(cert.get_absolute_url(), self.form_kwargs)
        # Not rendering confirmation checkbox value
        self.form_kwargs.pop('attested')
        for value in self.form_kwargs.values():
            self.assertContains(response, value)
        self.assertTemplateUsed(response, 'certificate/details-edit.html')
        message = list(response.context['messages']).pop()
        self.assertEqual(message.message, CertificateView.REVIEW_MSG)

    def test_auditor_denied_on_post(self):
        """Auditors cannot POST"""
        load_groups()
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(Group.objects.get(name='Auditor'))
        cert = mommy.make(Certificate, status=Certificate.ASSIGNED)
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        self.assertTemplateUsed(response, '403.html')

    def test_auditors_can_get(self):
        """Auditors can GET"""
        load_groups()
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(Group.objects.get(name='Auditor'))
        cert = mommy.make(Certificate, status=Certificate.ASSIGNED)
        """User gets an editable form if certificate is editable"""
        response = self.c.get(cert.get_absolute_url())
        self.assertTemplateUsed(response, 'certificate/details-edit.html')


class CertificateListViewTests(TestCase):

    def setUp(self):
        self.c = Client()
        self.url = reverse('certificates')

    def test_login_required(self):
        """redirect to login if anonymoususer"""
        response = self.c.get(self.url)
        target_url = settings.LOGIN_URL + '?next=' + self.url
        self.assertRedirects(response, target_url,
                             fetch_redirect_response=False)


class CertificateVoidTests(TestCase):

    def setUp(self):
        self.user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=True)
        self.c = Client()
        self.c.force_login(self.user)

    def test_auditor_denied(self):
        """Auditors cannot access"""
        load_groups()
        cert = mommy.make(Certificate, void=False)
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(Group.objects.get(name='Auditor'))
        response = self.c.get(reverse('void', args=[cert.number]), follow=True)
        self.assertTemplateUsed(response, '403.html')

    def test_redirect_to_details_if_void(self):
        """
        Redirect w/ message to details if certificate is already voided
        """
        cert = mommy.make(Certificate, void=True)
        response = self.c.get(reverse('void', args=[cert.number]), follow=True)
        self.assertRedirects(response, cert.get_absolute_url())
        message = list(response.context['messages']).pop()
        self.assertEqual(message.message, CertificateVoidView.ALREADY_VOID)

    def test_render_void_form_w_choices(self):
        """
        Void form is rendered with choices defined by Certificate model
        """
        cert = mommy.make(Certificate, void=False)
        mommy.make('VoidReason', _quantity=2)
        response = self.c.get(reverse('void', args=[cert.number]), follow=True)
        for choice in Certificate.get_void_reasons():
            self.assertContains(response, choice)


class ExportViewTests(TestCase):

    def setUp(self):
        self.super_user = mommy.make(
            settings.AUTH_USER_MODEL, is_superuser=True)
        self.user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        self.cert = mommy.make(Certificate)
        self.c = Client()
        self.c.force_login(self.user)
        self.url = reverse('export')

    def test_yields_rows_for_each_certificate_none(self):
        """Only BOM and headers yielded if no certs visible"""
        response = self.c.get(self.url)
        results = [row for row in response.streaming_content]
        self.assertEqual(len(results), 2)

    def test_yields_rows_for_all_certificates_visible(self):
        """One row per certificates to which a user has access"""
        self.c.force_login(self.super_user)
        mommy.make(Certificate)
        response = self.c.get(self.url)
        results = [row for row in response.streaming_content]
        self.assertEqual(len(results), 2 + Certificate.objects.count())


class LicenseeDetailsViewTests(TestCase):

    def setUp(self):
        self.user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=True)
        self.licensee = mommy.make('Licensee')
        self.user.profile.licensees.add(self.licensee)
        self.url = reverse('licensee', args=[self.licensee.id])
        self.c = Client()
        self.c.force_login(self.user)

    def test_contacts_list_on_licensee_page(self):
        """Contact information is displayed on licensee page"""
        self.user.profile.phone_number = '555'
        self.user.save()
        response = self.c.get(self.url)
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.profile.phone_number)


class CertificateConfirmViewTest(CertTestCase):

    def setUp(self):
        super().setUp()
        self.cert = mommy.make(Certificate, status=Certificate.ASSIGNED)
        self.url = reverse('confirm', args=[self.cert.number])

    def test_auditor_denied(self):
        """Auditors cannot access"""
        load_groups()
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(Group.objects.get(name='Auditor'))
        response = self.c.post(self.url, self.form_kwargs)
        self.assertTemplateUsed(response, '403.html')

    def test_certificate_issued_on_post(self):
        self.c.post(self.url, self.form_kwargs)
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.status, Certificate.PREPARED)

    def test_certificate_not_issued_on_post_w_invalid_form(self):
        """If form is invalid, certificate not updated"""
        self.form_kwargs.pop('attested')
        self.c.post(self.url, self.form_kwargs)
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.status, Certificate.ASSIGNED)


class CertificateJsonTests(SimpleTestCase):

    def test_json_contains_all_physical_cert_fields(self):
        """Data returned must contain all physical certificate fields"""
        returned_columns = set(CertificateJson.columns)
        physical_fields = set(Certificate.PHYSICAL_FIELDS)
        self.assertTrue(physical_fields.issubset(returned_columns))
