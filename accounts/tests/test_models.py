from django.test import TestCase
from model_mommy import mommy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from accounts.models import Profile

User = get_user_model()


class ProfileTests(TestCase):
    fixtures = ['groups.json']

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
        """Superusers can see all certiticates"""
        mommy.make('Certificate')
        user = mommy.make(User, is_superuser=True)
        self.assertEqual(user.profile.certificates().count(), 1)

    def test_certs_returns_all_for_auditors(self):
        """Auditors can see all certiticates"""
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
