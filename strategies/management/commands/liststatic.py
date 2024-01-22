from django.core.management.base import BaseCommand
from django.contrib.staticfiles import finders

class Command(BaseCommand):
    help = 'List static files that Django can find'

    def handle(self, *args, **kwargs):
        for finder in finders.get_finders():
            for path, storage in finder.list([]):
                self.stdout.write(path)
