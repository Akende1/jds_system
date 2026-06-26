from django.core.management.base import BaseCommand

from sync.services import run_full_sync


class Command(BaseCommand):
    help = 'Run push then pull sync in one pass.'

    def add_arguments(self, parser):
        parser.add_argument('--device-id', default='local')

    def handle(self, *args, **options):
        result = run_full_sync(device_id=options['device_id'])
        self.stdout.write(
            self.style.SUCCESS(
                'Full sync completed: '
                f"push={result['push_log'].records_pushed}, "
                f"pull={result['pull_log'].records_pulled}, "
                f"pull-issues={result['pull_log'].records_failed}"
            )
        )