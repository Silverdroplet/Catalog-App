from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

class HomeViewTest(TestCase):
    def test_homepage_status_code(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)

    def test_homepage_template(self):
        response = self.client.get(reverse('core:home'))
        self.assertTemplateUsed(response, 'home.html')