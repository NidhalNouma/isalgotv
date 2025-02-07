from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
import stripe
from django.http import HttpResponse  
import time

from ..middleware import check_user_and_stripe_middleware
from ..models import User_Profile

from django.conf import settings
PRICE_LIST = settings.PRICE_LIST

class MiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create(username='testuser', password='password')
        self.get_response = lambda request: HttpResponse("Dummy response")
        self.middleware = check_user_and_stripe_middleware(self.get_response)

    @patch('stripe.Customer.create')
    @patch('stripe.Customer.retrieve')
    @patch('stripe.Subscription.retrieve')
    @patch('stripe.Invoice.upcoming')
    def test_new_user_without_customer_id(self, mock_upcoming, mock_retrieve_subscription, mock_retrieve_customer, mock_create_customer):
        mock_create_customer.return_value = MagicMock(id='cust_1234')
        mock_retrieve_customer.return_value = MagicMock(id='cust_1234')
        mock_retrieve_subscription.return_value = MagicMock(status='active', plan=MagicMock(id='plan_id', interval='year', interval_count=1, currency='usd', active=True), current_period_end=time.time() + 10000)
        mock_upcoming.return_value = MagicMock(amount_due=2000)

        request = self.factory.get(reverse('home'))
        request.user = self.user

        # Assume middleware processes the request
        response = self.middleware(request)

        # Assert conditions or modifications to the request
        self.assertTrue(hasattr(request, 'user_profile'))
        self.assertTrue(hasattr(request.user_profile, 'customer_id'))
        self.assertEqual(request.user_profile.customer_id, 'cust_1234')
        self.assertFalse(request.has_subscription)
        self.assertEqual(response.status_code, 200)

    @patch('stripe.Customer.create')
    @patch('stripe.Customer.retrieve')
    @patch('stripe.Subscription.retrieve')
    @patch('stripe.Invoice.upcoming')
    def test_existing_user_with_customer_id(self, mock_upcoming, mock_retrieve_subscription, mock_retrieve_customer, mock_create_customer):
        # Setup the existing user and profile
        existing_user = User.objects.create(username='existinguser', password='securepassword')
        existing_profile = User_Profile.objects.create(user=existing_user, customer_id='existing_cust_1234', subscription_id='sub_123')
        
        # Mock the stripe calls
        mock_retrieve_customer.return_value = MagicMock(id='existing_cust_1234')
        mock_retrieve_subscription.return_value = MagicMock(id= "sub_123",status='active', plan=MagicMock(id='existing_plan_id', interval='month', interval_count=1, currency='usd', active=True), current_period_end=time.time() + 10000)
        mock_upcoming.return_value = MagicMock(amount_due=1500)

        # Create request for the existing user
        request = self.factory.get(reverse('home'))
        request.user = existing_user
        
        # Run the middleware
        response = self.middleware(request)
        
        # Assertions to check the correct handling of existing user
        self.assertTrue(hasattr(request, 'user_profile'))
        self.assertEqual(request.user_profile.customer_id, 'existing_cust_1234')
        self.assertTrue(request.has_subscription)
        self.assertEqual(response.status_code, 200)