# from django.test import TestCase, Client, RequestFactory
# from django.contrib.auth.models import User
# from django.urls import reverse
# from unittest.mock import patch, Mock
# from profile_user.models import User_Profile
# from strategies.models import Strategy, StrategyResults, StrategyComments
# from profile_user.middleware import check_user_and_stripe_middleware
# import stripe

# # class CheckUserAndStripeMiddlewareTests(TestCase):
# #     def setUp(self):
# #         self.factory = RequestFactory()
# #         self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass')
# #         self.get_response = Mock()  # Simulates the next middleware or view
# #         self.middleware = check_user_and_stripe_middleware(self.get_response)

# #     @patch('stripe.Customer.retrieve')
# #     @patch('stripe.Subscription.retrieve')
# #     @patch('stripe.Invoice.upcoming')
# #     def test_middleware_with_active_user(self, mock_upcoming, mock_retrieve_sub, mock_retrieve_cust):
# #         # Setup mock return values
# #         mock_retrieve_cust.return_value = Mock(spec=stripe.Customer, id='cus_example')
# #         print(mock_retrieve_cust.return_value)
# #         mock_retrieve_sub.return_value = Mock(spec=stripe.Subscription, status='active', current_period_end=1700000000, plan=Mock(active=True, id='plan_example'))
# #         mock_upcoming.return_value = {'amount_due': 2000}

# #         # Create request
# #         request = self.factory.get(reverse('home'))
# #         request.user = self.user

# #         # Run middleware
# #         response = self.middleware(request)

# #         print(request)

# #         # Assertions
# #         self.assertTrue(request.has_subscription)
# #         self.assertEqual(request.subscription_status, 'active')

# #         # Check response (if necessary)
# #         self.get_response.assert_called_once_with(request)

# class HomeViewTests(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.user = User.objects.create_user(username="testuser", password="password123")
#         self.profile = User_Profile.objects.create(user=self.user)
#         self.home_url = reverse('home')  # Replace 'home' with your actual URL name.

#     def test_home_no_subscription(self):
#         self.client.login(username="testuser", password="password123")
#         response = self.client.get(self.home_url)
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'home.html')
#         self.assertEqual(response.context['step'], 1)
        

#     @patch('profile_user.middleware.check_user_and_stripe_middleware')
#     def test_home_with_subscription(self, mock_process_request):
#         mock_process_request.return_value.has_subscription = True
#         mock_process_request.return_value.subscription_status = 'active'

#         self.client.login(username="testuser", password="password123")
#         response = self.client.get(self.home_url)
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.context['step'], 2)

#     # def test_home_with_tradingview_username(self):
#     #     self.profile.has_subscription = True
#     #     self.profile.subscription_status = 'active'
#     #     self.profile.tradingview_username = "test_tradingview_user"
#     #     self.profile.save()

#     #     self.client.login(username="testuser", password="password123")
#     #     response = self.client.get(self.home_url)
#     #     self.assertEqual(response.status_code, 200)
#     #     self.assertEqual(response.context['step'], 4)

#     # def test_home_query_step_3(self):
#     #     self.profile.has_subscription = True
#     #     self.profile.subscription_status = 'active'
#     #     self.profile.tradingview_username = "test_tradingview_user"
#     #     self.profile.save()

#     #     self.client.login(username="testuser", password="password123")
#     #     response = self.client.get(self.home_url + '?step=3')
#     #     self.assertEqual(response.status_code, 200)
#     #     self.assertEqual(response.context['step'], 3)

#     # @patch('profile_user.views.Strategy.objects.filter')
#     # @patch('profile_user.views.StrategyResults.objects.all')
#     # @patch('profile_user.views.StrategyComments.objects.all')
#     # def test_home_context_step_4(self, mock_comments, mock_results, mock_strategies):
#     #     mock_strategies.return_value.order_by.return_value = ["strategy1", "strategy2"]
#     #     mock_results.return_value.order_by.return_value = ["result1", "result2"]
#     #     mock_comments.return_value.order_by.return_value = ["comment1", "comment2"]

#     #     self.profile.has_subscription = True
#     #     self.profile.subscription_status = 'active'
#     #     self.profile.tradingview_username = "test_tradingview_user"
#     #     self.profile.save()

#     #     self.client.login(username="testuser", password="password123")
#     #     response = self.client.get(self.home_url)
#     #     self.assertEqual(response.status_code, 200)
#     #     self.assertEqual(response.context['step'], 4)
#     #     self.assertIn('new_strategies', response.context)
#     #     self.assertIn('new_results', response.context)