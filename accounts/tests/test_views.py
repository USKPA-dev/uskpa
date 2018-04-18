from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from model_mommy import mommy

from accounts.views import UserProfileView


class ProfileChangeViewTests(TestCase):

    def setUp(self):
        self.user = mommy.make(settings.AUTH_USER_MODEL,
                               first_name='TestFirst', last_name='TestLast')
        self.client = Client()
        self.client.force_login(self.user)
        self.url = reverse('profile')
        self.form_data = {'user-first_name': self.user.first_name, 'user-last_name': self.user.last_name,
                          'userprofile-phone_number': self.user.profile.phone_number}
        self.our_pw = 'ThisismytestingPW'

    def _set_pw(self):
        """set a known password and login"""
        self.user.set_password(self.our_pw)
        self.user.save()
        self.client.force_login(self.user)

    def test_login_required(self):
        """Cannot access if not logged in"""
        response = Client().get(self.url)
        self.assertRedirects(response, reverse('login') + '?next=' + self.url)

    def test_get_profile_page(self):
        """Can retrieve the profile page as a user"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile.html')

    def test_profile_page_has_users_data(self):
        """User's existing data is rendered on profile page"""
        response = self.client.get(self.url)
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)

    def test_profile_no_changes_if_forms_are_not_modified(self):
        """No data changes take place if the form is not modified on submit"""
        original_name = self.user.first_name

        response = self.client.post(self.url, data=self.form_data, follow=True)
        messages = [m.message for m in list(response.context['messages'])]

        self.user.refresh_from_db()
        self.assertEqual(original_name, self.user.first_name)
        self.assertIn(UserProfileView.NO_CHANGES_MESSAGE, messages)

    def test_user_model_changes(self):
        """Fields on user model can be modified"""
        original_name = self.user.first_name
        self.form_data.update({'user-first_name': 'NEW NAME'})

        response = self.client.post(self.url, data=self.form_data, follow=True)
        messages = [m.message for m in list(response.context['messages'])]

        self.user.refresh_from_db()
        self.assertNotEqual(original_name, self.user.first_name)
        self.assertEqual('NEW NAME', self.user.first_name)
        self.assertIn(UserProfileView.PROFILE_CHANGED_MESSAGE, messages)

    def test_profile_model_changes(self):
        """Fields on Profile model can be modified"""
        original_num = self.user.profile.phone_number
        new_number = '555-555-5555'
        self.form_data.update({'userprofile-phone_number': new_number})

        response = self.client.post(self.url, data=self.form_data, follow=True)
        messages = [m.message for m in list(response.context['messages'])]

        self.user.refresh_from_db()
        self.assertNotEqual(original_num, self.user.profile.phone_number)
        self.assertEqual(new_number, self.user.profile.phone_number)
        self.assertIn(UserProfileView.PROFILE_CHANGED_MESSAGE, messages)

    def test_password_changes(self):
        """Password can be modified"""
        self._set_pw()
        new_pw = 'ThisismyNEWtestingPW'

        self.form_data.update({'old_password': self.our_pw, 'new_password1': new_pw, 'new_password2': new_pw})
        response = self.client.post(self.url, data=self.form_data, follow=True)
        messages = [m.message for m in list(response.context['messages'])]

        self.assertTemplateUsed(response, 'login.html')
        self.assertIn(UserProfileView.PASSWORD_CHANGED_MESSAGE, messages)

    def test_can_change_profile_and_password(self):
        """Password can be changed at same time as profile"""
        self._set_pw()
        new_pw = 'ThisismyNEWtestingPW'
        original_num = self.user.profile.phone_number
        new_number = '555-555-5555'

        self.form_data.update({'old_password': self.our_pw, 'new_password1': new_pw,
                              'new_password2': new_pw, 'userprofile-phone_number': new_number})
        response = self.client.post(self.url, data=self.form_data, follow=True)
        messages = [m.message for m in list(response.context['messages'])]

        self.user.refresh_from_db()
        self.assertTemplateUsed(response, 'login.html')
        self.assertNotEqual(original_num, self.user.profile.phone_number)
        self.assertEqual(new_number, self.user.profile.phone_number)
        self.assertIn(UserProfileView.PROFILE_CHANGED_MESSAGE, messages)
        self.assertIn(UserProfileView.PASSWORD_CHANGED_MESSAGE, messages)

    def test_invalid_pw_change(self):
        """No changes made if password change validation fails"""
        original_num = self.user.profile.phone_number
        new_number = '555-555-5555'
        new_pw = 'partialNewPassword'
        self.form_data.update({'old_password': 'NOT OUR PW',
                              'new_password2': new_pw, 'userprofile-phone_number': new_number})
        response = self.client.post(self.url, data=self.form_data, follow=True)
        self.assertContains(response, 'Password change failed')
        self.user.refresh_from_db()
        self.assertTemplateUsed(response, 'profile.html')
        self.assertEqual(original_num, self.user.profile.phone_number)
