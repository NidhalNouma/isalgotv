from django.core.management.base import BaseCommand, CommandError
from strategies.models import *

class Command(BaseCommand):
    help = 'Deletes all Strategy objects from the database'

    def handle(self, *args, **options):
        confirm = input("Are you sure you want to delete all Strategy objects? (yes/no): ")

        if confirm.lower() != 'yes':
            raise CommandError("Deletion aborted. No changes made.")
        
        # Delete all Strategy objects from the database
        Strategy.objects.all().delete()
        StrategyImages.objects.all().delete()
        # StrategyComments.objects.all().delete(force=True)
        # StrategyResults.objects.all().delete(force=True)

        self.stdout.write(self.style.SUCCESS("All Strategy objects have been deleted."))
