from django.core.management.base import BaseCommand
from faker import Faker
from django.contrib.auth.models import User
from strategies.models import Strategy, StrategyImages, StrategyResults, StrategyComments
from django.utils import timezone
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType

from django.utils.text import slugify
import random

class Command(BaseCommand):
    help = 'Creates random Strategy objects with associated StrategyImages, StrategyResults, and StrategyComments'

    def add_arguments(self, parser):
        parser.add_argument('num_strategies', type=int, default=10, help='Number of random strategies to create')

    def handle(self, *args, **options):
        num_strategies = options['num_strategies']
        fake = Faker()

        for _ in range(num_strategies):
            strategy = self.create_random_strategy(fake)
            self.create_random_comments(fake, strategy)
            self.create_random_results(fake, strategy)
            self.create_random_images(fake, strategy)

    def create_fake_user(self, fake):
        # Create and return a fake User object
        user = User.objects.create_user(
            username=fake.user_name(),
            email=fake.email(),
            password=fake.password(),
        )
        return user

    def create_random_strategy(self, fake):
        # Create a random strategy
        random_name = fake.catch_phrase()
        strategy = Strategy.objects.create(
            type=random.choice([x[0] for x in Strategy.TYPE]),
            version="1.0",
            name=random_name,
            description=fake.paragraph(),
            content=fake.text(),
            created_at=timezone.now(),
            updated_at=timezone.now(),
            tradingview_ID=f"TV_{fake.random_int(10000, 99999)}",
            tradingview_url=f"https://tradingview.com/{slugify(random_name)}",
            video_url=f"https://youtube.com/{slugify(random_name)}",
            created_by=User.objects.first(),
            settings={},
            settings_types={},
        )
        return strategy

    def create_random_comments(self, fake, strategy):
        # Create random comments for the strategy
        for _ in range(fake.random_int(0, 5)):
            StrategyComments.objects.create(
                created_by=User.objects.first(),
                created_at=timezone.now(),
                description=fake.paragraph(),
                strategy=strategy,
            )

    def create_random_results(self, fake, strategy):
        # Create random results for the strategy
        for _ in range(fake.random_int(1, 5)):
            test_start_at = timezone.make_aware(fake.date_time_this_decade())
            test_end_at = test_start_at + timezone.timedelta(days=fake.random_int(1, 365))
            StrategyResults.objects.create(
                strategy=strategy,
                created_by=User.objects.first(),
                created_at=timezone.now(),
                settings={},
                description=fake.paragraph(),
                test_start_at=test_start_at,
                test_end_at=test_end_at,
                time_frame_int=fake.random_int(1, 10),
                time_frame=random.choice([x[0] for x in StrategyResults.TIME_FRAME]),
                pair=f"Pair-{fake.random_int(1, 100)}",
                net_profit=fake.pyfloat(positive=True, max_value=100),
                net_profit_percentage=fake.pyfloat(positive=True, max_value=100),
                max_drawdown=fake.pyfloat(positive=True, max_value=100),
                max_drawdown_percentage=fake.pyfloat(positive=True, max_value=100),
                profit_factor=fake.pyfloat(positive=True, max_value=10),
                profitable_percentage=fake.pyfloat(positive=True, max_value=100),
                total_trade=fake.random_int(1, 100),
            )

    def create_random_images(self, fake, strategy):
        # Create random images for the strategy
        for _ in range(fake.random_int(1, 3)):
            name = fake.word()

            content_type = ContentType.objects.get_for_model(strategy)
            StrategyImages.objects.create(
                name=name,
                img=f"strategies_images/{slugify(name)}.jpg",
                created_at=timezone.now(),
                content_type=content_type,
                object_id=strategy.id,
            )

