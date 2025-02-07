# from django.test import TestCase, TransactionTestCase
# from faker import Faker
# from django.contrib.auth.models import User
# from .models import *
# from datetime import timedelta, datetime
# from django.utils import timezone


# class StrategyTestCase(TestCase):

#     @classmethod
#     def setUpTestData(cls):
#         cls.fake = Faker()
#         cls.random_objects = []
#         for _ in range(10):
#             strategy = Strategy.objects.create(
#                 type=cls.fake.random_element(elements=("S", "I")),
#                 version=cls.fake.random_number(digits=1, fix_len=True),
#                 name=cls.fake.company(),
#                 description=cls.fake.text(),
#                 content=cls.fake.paragraph(),
#                 tradingview_ID=cls.fake.uuid4(),
#                 tradingview_url=cls.fake.url(),
#                 video_url=cls.fake.url(),
#                 created_by=cls.create_fake_user(),
#                 settings=cls.create_fake_settings(),
#                 settings_types=cls.create_fake_settings_types(),
#             )
#             cls.random_objects.append(strategy)
        

#     @classmethod
#     def create_fake_user(cls):
#         # Create and return a fake User object
#         user = User.objects.create_user(
#             username=cls.fake.user_name(),
#             email=cls.fake.email(),
#             password=cls.fake.password(),
#         )
#         return user
    
#     @classmethod
#     def create_fake_settings(cls):
#         # Create and return a fake settings dictionary
#         return {
#             "setting1": cls.fake.random_element(elements=("Value1", "Value2", "Value3")),
#             "setting2": cls.fake.random_number(digits=3),
#             # Add more settings as needed
#         }

#     @classmethod
#     def create_fake_settings_types(cls):
#         # Create and return a fake settings types dictionary
#         return {
#             "setting1": cls.fake.random_element(elements=("String", "Number", "Enum")),
#             "setting2": "Number",
#             # Add more setting types as needed
#         }

#     def test_random_objects_exist(self):
#         # Access the created random objects in your test
#         for strategy in self.random_objects:
#             # Test logic using the random objects
#             self.assertTrue(isinstance(strategy, Strategy))

#     # def setUp(self):
#     #     self.fake = Faker()

#     # def create_fake_strategy(self):
#     #     # Create and return a fake Strategy object
#     #     strategy = Strategy.objects.create(
#     #         type=self.fake.random_element(elements=("S", "I")),
#     #         version=self.fake.random_number(digits=1, fix_len=True),
#     #         name=self.fake.company(),
#     #         description=self.fake.text(),
#     #         content=self.fake.paragraph(),
#     #         tradingview_ID=self.fake.uuid4(),
#     #         tradingview_url=self.fake.url(),
#     #         video_url=self.fake.url(),
#     #         created_by=self.create_fake_user(),
#     #         settings=self.create_fake_settings(),
#     #         settings_types=self.create_fake_settings_types(),
#     #     )

#     #     # Add related images and results
#     #     for _ in range(5):
#     #         strategy.imagees.add(self.create_fake_image())
#     #         strategy.results.add(self.create_fake_result())

#     #     return strategy

#     # def create_fake_user(self):
#     #     # Create and return a fake User object
#     #     user = User.objects.create_user(
#     #         username=self.fake.user_name(),
#     #         email=self.fake.email(),
#     #         password=self.fake.password(),
#     #     )
#     #     return user

#     # def create_fake_image(self):
#     #     # Create and return a fake StrategyImages object
#     #     return StrategyImages.objects.create(
#     #         name=self.fake.word(),
#     #         img=self.fake.image_url(),
#     #     )

#     # def create_fake_result(self):
#     #     # Create and return a fake StrategyResults object

#     #     start_date = self.fake.date_time_between(start_date='-30d', end_date='now', tzinfo=timezone.utc)
#     #     end_date = start_date + timedelta(days=7)
#     #     return StrategyResults.objects.create(
#     #         created_by=self.create_fake_user(),
#     #         time_frame=self.fake.random_element(elements=("S", "M", "H", "W", "Mn", "R")),
#     #         pair=self.fake.word(),
#     #         net_profit=self.fake.random_number(digits=5) / 100,
#     #         net_profit_percentage=self.fake.random_number(digits=2) / 100,
#     #         max_drawdown=self.fake.random_number(digits=5) / 100,
#     #         max_drawdown_percentage=self.fake.random_number(digits=2) / 100,
#     #         profit_factor=self.fake.random_number(digits=5) / 100,
#     #         profitable_percentage=self.fake.random_number(digits=2) / 100,
#     #         total_trade=self.fake.random_number(digits=3),
#     #         test_start_at=start_date,
#     #         test_end_at=end_date,
#     #     )

#     # def create_fake_settings(self):
#     #     # Create and return a fake settings dictionary
#     #     return {
#     #         "setting1": self.fake.random_element(elements=("Value1", "Value2", "Value3")),
#     #         "setting2": self.fake.random_number(digits=3),
#     #         # Add more settings as needed
#     #     }

#     # def create_fake_settings_types(self):
#     #     # Create and return a fake settings types dictionary
#     #     return {
#     #         "setting1": self.fake.random_element(elements=("String", "Number", "Enum")),
#     #         "setting2": "Number",
#     #         # Add more setting types as needed
#     #     }

#     # def test_create_fake_strategies(self):
#     #     # Create 10 fake Strategy objects
#     #     for _ in range(10):
#     #         self.create_fake_strategy()


