from django.test import TestCase, RequestFactory
from django.core import mail
from django.contrib.auth import get_user_model

from accounts.forms import UserCreationForm
from accounts.admin import ProfileUserAdmin

User = get_user_model()


class ProfileAdminTests(TestCase):

    def setUp(self):

        self.form = UserCreationForm({'username': 'test', 'email': 'test@test.com'})
        self.user = self.form.save(commit=False)
        # We don't need to target the real URL here, just making an HttpRequest()
        self.request = RequestFactory().get('/')
        self.site = 'SITE'

    def test_email_on_user_add(self):
        """Send an email to the user on creation of their account"""
        ProfileUserAdmin(User, self.site).save_model(self.request, self.user, self.form, False,)
        self.assertEqual(len(mail.outbox), 1)

    def test_no_email_on_user_edit(self):
        """No emails generated when `change` is True, we're editing an existing User"""
        ProfileUserAdmin(User, self.site).save_model(self.request, self.user, self.form, True,)
        self.assertEqual(len(mail.outbox), 0)
