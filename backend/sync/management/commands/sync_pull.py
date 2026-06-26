from django.core.management.base import BaseCommand

from sync.services import run_pull_sync


class Command(BaseCommand):
    help = 'Pull remote changes and record sync status.'

    def add_arguments(self, parser):
        parser.add_argument('--device-id', default='local')

    def handle(self, *args, **options):
        log = run_pull_sync(device_id=options['device_id'])
        self.stdout.write(self.style.SUCCESS(f'Pull sync completed: {log.records_pulled} record(s) pulled, {log.records_failed} issue(s) flagged.'))