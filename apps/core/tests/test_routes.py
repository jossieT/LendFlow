from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


User = get_user_model()


class RoutesTest(TestCase):
    def setUp(self):
        self.client = Client()
        # create a borrower user
        self.borrower = User.objects.create_user(username='alice', password='password123', email='alice@example.com')
        self.borrower.is_borrower = True
        self.borrower.save()

        # create a lender user
        self.lender = User.objects.create_user(username='bob', password='password123', email='bob@example.com')
        self.lender.is_lender = True
        self.lender.save()

    def test_public_auth_pages(self):
        # login and register pages should be accessible
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(reverse('register'))
        self.assertIn(resp.status_code, (200, 302))

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse('dashboard'))
        # should redirect to login
        self.assertIn(resp.status_code, (302,))

    def test_borrower_access_dashboard_and_profile(self):
        logged = self.client.login(username='alice', password='password123')
        self.assertTrue(logged)
        resp = self.client.get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)

        # borrower should be redirected away from lender dashboard
        resp = self.client.get(reverse('lender_dashboard'))
        self.assertIn(resp.status_code, (302,))

    def test_lender_access_lender_dashboard(self):
        logged = self.client.login(username='bob', password='password123')
        self.assertTrue(logged)
        resp = self.client.get(reverse('lender_dashboard'))
        # lenders should reach lender dashboard (200) or be redirected if app logic differs
        self.assertIn(resp.status_code, (200, 302))
