import datetime
import json

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from model_mommy import mommy
from django.core import mail

from kpc.forms import LicenseeCertificateForm, StatusUpdateForm
from kpc.models import Certificate, CertificateConfig, EditRequest, Receipt
from kpc.tests import CERT_FORM_KWARGS, load_initial_data
from kpc.views import (CertificateRegisterView, CertificateView,
                       CertificateVoidView, ExportView, licensee_contacts)


def _get_expiry_date(date_of_issue):
    """determine expiry date"""
    issued = datetime.datetime.strptime(date_of_issue, "%m/%d/%Y").date()
    date_of_expiry = issued + \
        datetime.timedelta(days=Certificate.get_expiry_days())
    return date_of_expiry.strftime('%m/%d/%Y')


class HomePageTests(TestCase):

    def setUp(self):
        self.c = Client()

    def test_irs_docs_rendered_on_homepage(self):
        """
        Links to documents in ./static/uskpa_documents/irs/ are rendered on home page
        """
        response = self.c.get('')
        kpc_config = apps.get_app_config('kpc')
        irs_docs = [f[1] for f in kpc_config._get_irs_docs()]
        for doc in irs_docs:
            self.assertContains(response, doc)


class CertTestCase(TestCase):

    def get_form_kwargs(self):
        base_kwargs = CERT_FORM_KWARGS.copy()
        base_kwargs['harmonized_code'] = mommy.make('HSCode').id
        base_kwargs['port_of_export'] = mommy.make('PortOfExport').id
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
                            'cert_list': '201,123456'}
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
        receipt = Receipt.objects.first()
        success_msg = CertificateRegisterView.get_success_msg(5, receipt)
        self.assertEqual(message.message, success_msg)

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
        receipt = Receipt.objects.first()
        success_msg = CertificateRegisterView.get_success_msg(2, receipt)
        self.assertEqual(message.message, success_msg)

    def test_receipt_generated_with_all_input(self):
        """Receipt created containing all registration details"""
        client = Client()
        client.force_login(self.admin_user)
        self.form_kwargs.update(self.list_kwargs)

        client.post(reverse('cert-register'), self.form_kwargs)

        receipt = Receipt.objects.first()
        response = client.get(receipt.get_absolute_url())

        requested_cert_list = self.form_kwargs['cert_list'].split(',')
        expected_certs = ', '.join([f'US{num}' for num in requested_cert_list])

        self.assertContains(response, self.licensee.name)
        self.assertContains(response, f'Receipt #{receipt.number}')
        self.assertContains(response, self.licensee.address)
        self.assertContains(response, self.user.profile)
        self.assertContains(response, self.form_kwargs['payment_amount'])
        self.assertContains(response, expected_certs)
        self.assertContains(response, f'${CertificateConfig.get_solo().price}')
        self.assertContains(response, '2 certificates')


class CertificateViewTests(CertTestCase):

    def test_cannot_access_if_licensee_inactive(self):
        """Certificate cannot be accessed by contact if licensee if not active"""
        licensee = mommy.make('Licensee', is_active=False)
        user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        user.profile.licensees.add(licensee)
        self.c.force_login(user)
        cert = mommy.make(Certificate, licensee=licensee)
        response = self.c.get(cert.get_absolute_url())
        self.assertEqual(response.status_code, 403)

    def test_status_form_when_not_editable(self):
        """
        status form is used when certificate is not editable
        by licensees
        """
        cert = mommy.make(Certificate, status=Certificate.SHIPPED)
        form = CertificateView(object=cert).get_form_class()
        self.assertIs(form, StatusUpdateForm)

    def test_cert_form_when_editable(self):
        """Licensee form is used when certificate is  editable"""
        cert = mommy.make(Certificate, status=Certificate.AVAILABLE)
        form = CertificateView(object=cert).get_form_class()
        self.assertIs(form, LicenseeCertificateForm)

    def test_editable_form_rendered_if_available(self):
        cert = mommy.make(Certificate, status=Certificate.AVAILABLE)
        """User gets an editable form if certificate is editable"""
        response = self.c.get(cert.get_absolute_url())
        self.assertTemplateUsed(response, 'certificate/prepare.html')

    def test_non_editable_form_rendered_if_available(self):
        """User gets a non-editable form if certificate is editable"""
        cert = mommy.make(Certificate, status=Certificate.VOID)
        response = self.c.get(cert.get_absolute_url())
        self.assertTemplateUsed(response, 'certificate/details.html')

    def test_form_invalid_if_cert_is_not_available(self):
        """Users can't use this form if certificate is not AVAILABLE"""
        cert = mommy.make(Certificate, status=Certificate.VOID)
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        self.assertContains(response, StatusUpdateForm.NOT_AVAILABLE)

    def test_form_invalid_if_not_all_fields_provided(self):
        """Form invalid without all fields"""
        cert = mommy.make(Certificate, status=Certificate.AVAILABLE)
        self.form_kwargs.pop('consignee')
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        cert.refresh_from_db()
        self.assertEqual(cert.status, Certificate.AVAILABLE)
        self.assertTemplateUsed(response, 'certificate/prepare.html')
        self.assertContains(response, 'required')

    def test_next_status_input_rendered_when_moddable(self):
        """Button to advance status is rendered if status can be changed"""
        cert = mommy.make(Certificate, status=Certificate.SHIPPED)
        response = self.c.get(cert.get_absolute_url())
        self.assertContains(
            response, f'Set status to: {cert.next_status_label}')

    def test_next_status_input_not_rendered_when_unmoddable(self):
        """Button to advance status is NOT rendered if status cannot be changed"""
        cert = mommy.make(Certificate, status=Certificate.VOID)
        response = self.c.get(cert.get_absolute_url())
        self.assertNotContains(response, 'Set status')

    def test_form_valid_if_cert_is_available(self):
        """Cert unchanged and confirmation template displayed w/ valid form"""
        cert = mommy.make(Certificate, status=Certificate.AVAILABLE)
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        cert.refresh_from_db()
        self.assertEqual(cert.status, Certificate.AVAILABLE)
        self.assertTemplateUsed(response, 'certificate/preview.html')

    def test_fields_rendered_for_review(self):
        """Fields rendered for review template"""
        cert = mommy.make(Certificate, status=Certificate.AVAILABLE)
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        for field in self.form_kwargs.keys():
            self.assertContains(response, field)

    def test_pdf_preview_data_in_context(self):
        """Data for PDF preview is included in context"""
        cert = mommy.make(Certificate, status=Certificate.AVAILABLE)
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        self.assertTrue('b64_pdf' in response.context)

    def test_edit_form_for_changes_w_get_params(self):
        """When get params provided, render prepopulated form"""
        cert = mommy.make(Certificate, status=Certificate.AVAILABLE)
        response = self.c.get(cert.get_absolute_url(), self.form_kwargs)
        # Not rendering confirmation checkbox value
        self.form_kwargs.pop('attested')
        for value in self.form_kwargs.values():
            self.assertContains(response, value)
        self.assertTemplateUsed(response, 'certificate/prepare.html')
        message = list(response.context['messages']).pop()
        self.assertEqual(message.message, CertificateView.REVIEW_MSG)

    def test_auditor_denied_on_post(self):
        """Auditors cannot POST"""
        load_initial_data()
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(Group.objects.get(name='Auditor'))
        cert = mommy.make(Certificate, status=Certificate.AVAILABLE)
        response = self.c.post(cert.get_absolute_url(),
                               self.form_kwargs, follow=True)
        self.assertTemplateUsed(response, '403.html')

    def test_auditors_can_get(self):
        """Auditors can GET"""
        load_initial_data()
        self.user.is_superuser = False
        self.user.save()
        self.user.groups.add(Group.objects.get(name='Auditor'))
        cert = mommy.make(Certificate, status=Certificate.AVAILABLE)
        """User gets an editable form if certificate is editable"""
        response = self.c.get(cert.get_absolute_url())
        self.assertTemplateUsed(response, 'certificate/prepare.html')


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
        load_initial_data()
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
        self.cert = mommy.make(Certificate, status=Certificate.AVAILABLE)
        self.url = reverse('confirm', args=[self.cert.number])

    def test_auditor_denied(self):
        """Auditors cannot access"""
        load_initial_data()
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
        self.assertEqual(self.cert.status, Certificate.AVAILABLE)

    def test_certificate_issued_on_post_w_multi_origins(self):
        """
        Certificate can be prepared with MULTIPLE_ORIGIN_COUNTRY_CODE for
        origin option selected
        """
        # Add multi_origin as validate country of origin
        multi_origin = settings.MULTIPLE_ORIGIN_COUNTRY_CODE
        config = CertificateConfig.get_solo()
        config.kp_countries = f'AQ,{multi_origin}'
        config.save()

        self.form_kwargs['country_of_origin'] = multi_origin
        self.c.post(self.url, self.form_kwargs)
        self.cert.refresh_from_db()
        self.assertEqual(self.cert.status, Certificate.PREPARED)


class CertificateJsonTests(SimpleTestCase):

    def test_json_contains_all_physical_cert_fields(self):
        """Data returned must contain all physical certificate fields"""
        returned_columns = set(ExportView.columns)
        physical_fields = set(Certificate.PHYSICAL_FIELDS)
        self.assertTrue(physical_fields.issubset(returned_columns))


def make_auditor():
    load_initial_data()
    user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
    user.groups.add(Group.objects.get(name='Auditor'))
    return user


class KpcAdressViewTests(TestCase):

    def setUp(self):
        self.destination = mommy.make('KpcAddress')
        self.licensee = self.destination.licensee
        self.c = Client()

    def test_auditor_cannot_add(self):
        user = make_auditor()
        self.c.force_login(user)
        response = self.c.get(reverse('new-addressee', args=[self.licensee.id]))
        self.assertEqual(403, response.status_code)

    def test_auditor_cannot_edit(self):
        user = make_auditor()
        self.c.force_login(user)
        response = self.c.get(self.destination.get_absolute_url())
        self.assertEqual(403, response.status_code)

    def test_auditor_cannot_delete(self):
        user = make_auditor()
        self.c.force_login(user)
        response = self.c.get(self.destination.get_delete_url())
        self.assertEqual(403, response.status_code)


class KpcAddressCreateTests(TestCase):

    def setUp(self):
        load_initial_data()
        self.licensee = mommy.make('Licensee')
        self.user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        self.user.profile.licensees.add(self.licensee)
        self.url = reverse('new-addressee', args=[self.licensee.id])
        self.c = Client()
        self.c.force_login(self.user)

    def test_contact_can_create_destination(self):
        """Licensee's contact can add destination to address book"""
        data = {'name': 'TEST', 'address': 'TEST', "country": 'AQ'}
        self.c.post(self.url, data=data)
        self.assertEqual(1, self.licensee.addresses.count())


class KpcAddressEditDeleteTests(TestCase):

    def setUp(self):
        load_initial_data()
        self.destination = mommy.make('KpcAddress', country='IN')
        self.licensee = self.destination.licensee
        self.user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        self.user.profile.licensees.add(self.licensee)
        self.url = self.destination.get_absolute_url()
        self.c = Client()
        self.c.force_login(self.user)

    def test_contact_can_create_destination(self):
        """Licensee's contact can edit destination"""
        data = {'name': 'TEST', 'address': 'TEST', "country": 'AQ'}
        self.c.post(self.url, data=data)
        self.destination.refresh_from_db()
        self.assertEqual('AQ', self.destination.country)

    def test_contact_can_delete_destination(self):
        """Licensee's contact can delete destination"""
        self.c.post(self.destination.get_delete_url())
        self.assertEqual(0, self.licensee.addresses.count())


class CertEditTestCase(TestCase):

    def _make_edit_form_kwargs(self):
        load_initial_data()
        form_kwargs = CERT_FORM_KWARGS.copy()
        form_kwargs.pop('attested')
        form_kwargs['harmonized_code'] = self.hs_code.id
        form_kwargs['port_of_export'] = self.poe.id
        form_kwargs['date_of_issue'] = '01/01/2018'
        form_kwargs['date_of_expiry'] = '03/02/2018'
        return form_kwargs

    def setUp(self):
        cert_kwargs = CERT_FORM_KWARGS.copy()
        self.poe = mommy.make('PortOfExport')
        self.hs_code = mommy.make('HSCode')
        cert_kwargs['harmonized_code'] = self.hs_code
        cert_kwargs['port_of_export'] = self.poe
        cert_kwargs['date_of_issue'] = '2018-01-01'
        cert_kwargs['date_of_expiry'] = '2018-03-02'

        self.cert = mommy.make('Certificate', **cert_kwargs)
        self.user = mommy.make(settings.AUTH_USER_MODEL,
                               is_superuser=True, email='test@test.com')
        self.c = Client()
        self.c.force_login(self.user)


class CertificateEditViewTests(CertEditTestCase):

    def setUp(self):
        super().setUp()

        self.url = reverse('edit', args=[self.cert.number])

    def test_edit_request_view_inaccessible_if_pending(self):
        """Edit request not accessible if one already exists and is pending"""
        load_initial_data()
        mommy.make('EditRequest', certificate=self.cert,
                   status=EditRequest.PENDING)
        response = self.c.get(self.url)
        self.assertRedirects(response, self.cert.get_absolute_url())

    def test_auditors_cannot_create_edit_requests(self):
        """Auditors cannot access edit request form"""
        auditor = make_auditor()
        self.c.force_login(auditor)
        response = self.c.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_form_valid_no_change_redirects(self):
        """No edit request created if no changes made on edit request form"""
        form_kwargs = self._make_edit_form_kwargs()
        response = self.c.post(self.url, form_kwargs, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(EditRequest.objects.exists())
        self.assertFalse(self.cert.pending_edit)

    def test_form_valid_change_creates_edit_request(self):
        """Edit request created if changes made on edit request form"""
        form_kwargs = self._make_edit_form_kwargs()
        form_kwargs['consignee'] = 'NEW CONSIGNEE'
        response = self.c.post(self.url, form_kwargs, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.cert.pending_edit.contact, self.user)


class EditRequestViewTests(CertEditTestCase):

    def setUp(self):
        """EditRequest with a single change to consignee field"""
        super().setUp()
        self.edit = mommy.make('EditRequest', certificate=self.cert, contact=self.user,
                               status=EditRequest.PENDING, consignee='NEWCONSIGNEE')
        self.url = self.edit.get_absolute_url()

    def test_cannot_post_without_perm(self):
        """
        accounts.can_adjudicate_edit_requests required
        to POST to this view
        """
        user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        self.c.force_login(user)
        response = self.c.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_can_post_with_perm(self):
        """
        accounts.can_adjudicate_edit_requests allows
        POSTing to this view

        User can view edit request but not approve/reject
        """
        load_initial_data()
        perm, _ = Permission.objects.get_or_create(codename='can_adjudicate_edit_requests')
        user = mommy.make(settings.AUTH_USER_MODEL, is_superuser=False)
        user.user_permissions.add(perm)
        licensee = mommy.make("Licensee")
        self.cert.licensee = licensee
        self.cert.save()

        user.profile.licensees.add(licensee)
        self.c.force_login(user)

        response = self.c.post(self.url)
        self.assertNotEqual(response.status_code, 403)

    def test_modified_values_displayed_on_page(self):
        """Previous and proposed values displayed on page"""
        response = self.c.get(self.url)
        self.assertContains(response, self.cert.consignee)
        self.assertContains(response, self.edit.consignee)

    def test_approve(self):
        """Certificate modified, reviewer set, and notification generated"""
        self.c.post(self.url, {'approve': True})
        self.assertEqual(len(mail.outbox), 1)
        self.edit.refresh_from_db()
        self.cert.refresh_from_db()
        self.assertEqual(self.edit.status, EditRequest.APPROVED)
        self.assertEqual(self.cert.consignee, self.edit.consignee)
        self.assertEqual(self.edit.reviewed_by, self.user)

    def test_reject(self):
        """Certificate NOT, reviewer set, and notification generated"""
        self.c.post(self.url, {'reject': True})
        self.assertEqual(len(mail.outbox), 1)
        self.edit.refresh_from_db()
        self.cert.refresh_from_db()
        self.assertEqual(self.edit.status, EditRequest.REJECTED)
        self.assertNotEqual(self.cert.consignee, self.edit.consignee)
        self.assertEqual(self.edit.reviewed_by, self.user)
