from django.test import TestCase
from model_mommy import mommy
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()


class ProfileTests(TestCase):

    def setUp(self):
        self.profile = mommy.prepare(Profile)

    def test_profile_returns_username_str(self):
        """String representation of profile is associated username"""
        self.assertEqual(str(self.profile), self.profile.user.username)

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
