from django.test import TestCase
from model_mommy import mommy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from accounts.models import Profile

User = get_user_model()


class ProfileTests(TestCase):
    fixtures = ['initial_data.json']

    def setUp(self):
        self.profile = mommy.prepare(Profile)

    def test_get_user_display_name_without_fullname(self):
        """String representation of profile is user's username if fullname absent"""
        self.assertEqual(self.profile.get_user_display_name(), self.profile.user.get_username())

    def test_get_user_display_name_with_fullname(self):
        """String representation of profile is user's fullname if present"""
        profile = mommy.prepare(Profile, user__first_name='test', user__last_name='test')
        self.assertEqual(profile.get_user_display_name(), profile.user.get_full_name())

    def test_profile_created_with_user(self):
        """Profile must be created along with a user model"""
        user = mommy.make(User)
        self.assertIsInstance(user.profile, Profile)

    def test_profile_updated_with_user(self):
        """Profile must be updated along with a user model"""
        user = mommy.make(User)
        user.profile.phone_number = 'NEW_VALUE'
        user.save()
        user.refresh_from_db()
        self.assertEqual(user.profile.phone_number, 'NEW_VALUE')

    def test_certs_returns_all_for_superusers(self):
        """Superusers can see all certificates"""
        mommy.make('Certificate')
        user = mommy.make(User, is_superuser=True)
        self.assertEqual(user.profile.certificates().count(), 1)

    def test_certs_returns_all_for_auditors(self):
        """Auditors can see all certificates"""
        mommy.make('Certificate')
        user = mommy.make(User, is_superuser=False)
        user.groups.add(Group.objects.get(name='Auditor'))
        self.assertEqual(user.profile.certificates().count(), 1)

    def test_certs_limited_by_licensees_for_users(self):
        """Users can only see certificates associated with their licensees"""
        licensee = mommy.make('Licensee')
        mommy.make('Certificate', licensee=licensee)
        user = mommy.make(User)
        self.assertEqual(user.profile.certificates().count(), 0)
        user.profile.licensees.add(licensee)
        self.assertEqual(user.profile.certificates().count(), 1)

    def test_certs_limited_by_active_licensees_for_users(self):
        """Users can only see certificates associated with their ACTIVE licensees"""
        licensee = mommy.make('Licensee')
        licensee_b = mommy.make('Licensee', is_active=False)

        mommy.make('Certificate', licensee=licensee)
        mommy.make('Certificate', licensee=licensee_b)
        user = mommy.make(User)
        user.profile.licensees.add(licensee)
        user.profile.licensees.add(licensee_b)
        self.assertEqual(user.profile.certificates().count(), 1)

    def test_address_book_url(self):
        """Address book url only provided if a user associated with a single licensee"""
        user = mommy.make(User)
        self.assertIsNone(user.profile.get_address_book_url())

        licensee = mommy.make('Licensee')
        user.profile.licensees.add(licensee)
        self.assertEqual(user.profile.get_address_book_url(), licensee.get_absolute_url())

        licensee_b = mommy.make('Licensee')
        user.profile.licensees.add(licensee_b)
        self.assertIsNone(user.profile.get_address_book_url())
