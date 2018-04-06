from django.test import SimpleTestCase
from model_mommy import mommy

from accounts.models import Profile


class ProfileTests(SimpleTestCase):

    def setUp(self):
        self.profile = mommy.prepare(Profile)

    def test_profile_returns_username_str(self):
        """String representation of profile is associated username"""
        self.assertEqual(str(self.profile), self.profile.user.username)
