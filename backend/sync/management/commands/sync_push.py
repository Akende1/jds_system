from django.core.management.base import BaseCommand

from sync.services import run_push_sync


class Command(BaseCommand):
    help = 'Push pending local changes into the sync queue.'

    def add_arguments(self, parser):
        parser.add_argument('--device-id', default='local')

    def handle(self, *args, **options):
        log = run_push_sync(device_id=options['device_id'])
        self.stdout.write(self.style.SUCCESS(f'Push sync completed: {log.records_pushed} record(s) processed.'))