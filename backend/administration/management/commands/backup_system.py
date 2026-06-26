"""
Management command for complete system backup (database + media)
Usage: python manage.py backup_system
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
from datetime import datetime


class Command(BaseCommand):
    help = 'Create a complete system backup (database + media files)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Directory to store backups (default: media/backups)'
        )
        parser.add_argument(
            '--compress-db',
            action='store_true',
            help='Compress database backup'
        )
        parser.add_argument(
            '--keep-days',
            type=int,
            default=30,
            help='Number of days to keep old backups (default: 30)'
        )
        parser.add_argument(
            '--skip-media',
            action='store_true',
            help='Skip media files backup'
        )
        parser.add_argument(
            '--skip-database',
            action='store_true',
            help='Skip database backup'
        )

    def handle(self, *args, **options):
        output_dir = options.get('output_dir')
        compress_db = options.get('compress_db')
        keep_days = options.get('keep_days')
        skip_media = options.get('skip_media')
        skip_database = options.get('skip_database')

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('🚀 COMPLETE SYSTEM BACKUP'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write('')

        # Setup backup directory
        if output_dir is None:
            output_dir = os.path.join(settings.MEDIA_ROOT, 'backups')
        
        db_backup_dir = os.path.join(output_dir, 'database')
        media_backup_dir = os.path.join(output_dir, 'media')
        
        success_count = 0
        failed_count = 0

        # Backup database
        if not skip_database:
            self.stdout.write(self.style.SUCCESS('📊 STEP 1: Database Backup'))
            self.stdout.write('-' * 60)
            try:
                call_command(
                    'backup_database',
                    output_dir=db_backup_dir,
                    compress=compress_db,
                    keep_days=keep_days
                )
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Database backup failed: {str(e)}'))
                failed_count += 1
            self.stdout.write('')

        # Backup media files
        if not skip_media:
            self.stdout.write(self.style.SUCCESS('📁 STEP 2: Media Files Backup'))
            self.stdout.write('-' * 60)
            try:
                call_command(
                    'backup_media',
                    output_dir=media_backup_dir,
                    keep_days=keep_days
                )
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Media backup failed: {str(e)}'))
                failed_count += 1
            self.stdout.write('')

        # Summary
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('BACKUP SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'Completed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write(f'Backup location: {output_dir}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✅ Successful backups: {success_count}'))
        
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Failed backups: {failed_count}'))
        else:
            self.stdout.write(self.style.SUCCESS('🎉 All backups completed successfully!'))
        
        self.stdout.write('')
        self.stdout.write('💡 Tips:')
        self.stdout.write('  - Schedule this command with cron or Task Scheduler for automated backups')
        self.stdout.write('  - Copy backup files to external storage for disaster recovery')
        self.stdout.write('  - Test restore procedure periodically to ensure backups are valid')
