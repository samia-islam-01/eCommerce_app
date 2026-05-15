from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class RegisterDuplicateEmailTest(TestCase):
    def setUp(self):
        User.objects.create_user(username='existing', password='pass1234', email='taken@example.com')

    def _post(self, username, email):
        return self.client.post(reverse('authenticator:register'), {
            'username': username,
            'password': 'pass1234',
            'password_confirm': 'pass1234',
            'email': email,
            'role': 'buyer',
        })

    def test_duplicate_email_rejected(self):
        response = self._post('newuser', 'taken@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'An account with this email address already exists.')
        self.assertFalse(User.objects.filter(username='newuser').exists())

    def test_unique_email_accepted(self):
        response = self._post('newuser', 'unique@example.com')
        self.assertRedirects(response, reverse('authenticator:welcome'))
        self.assertTrue(User.objects.filter(username='newuser').exists())