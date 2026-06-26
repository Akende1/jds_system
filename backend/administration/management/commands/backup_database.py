"""
Management command to backup the database
Usage: python manage.py backup_database [--output-dir DIR]
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
from datetime import datetime
import zipfile


class Command(BaseCommand):
    help = 'Create a backup of the SQLite database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Directory to store backup (default: media/backups/database)'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help='Compress backup into ZIP file'
        )
        parser.add_argument(
            '--keep-days',
            type=int,
            default=30,
            help='Number of days to keep old backups (default: 30)'
        )

    def handle(self, *args, **options):
        output_dir = options.get('output_dir')
        compress = options.get('compress')
        keep_days = options.get('keep_days')

        self.stdout.write(self.style.SUCCESS('🗄️  Starting database backup...'))

        # Get database path
        db_path = settings.DATABASES['default']['NAME']
        
        if not os.path.exists(db_path):
            self.stdout.write(self.style.ERROR(f'❌ Database file not found: {db_path}'))
            return

        # Setup backup directory
        if output_dir is None:
            output_dir = os.path.join(settings.MEDIA_ROOT, 'backups', 'database')
        
        os.makedirs(output_dir, exist_ok=True)

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'db_backup_{timestamp}.sqlite3'
        backup_path = os.path.join(output_dir, backup_filename)

        try:
            # Copy database file
            self.stdout.write(f'📋 Copying database...')
            shutil.copy2(db_path, backup_path)
            
            file_size = os.path.getsize(backup_path)
            size_mb = file_size / (1024 * 1024)
            
            self.stdout.write(self.style.SUCCESS(f'✅ Database backed up successfully!'))
            self.stdout.write(f'   File: {backup_path}')
            self.stdout.write(f'   Size: {size_mb:.2f} MB')

            # Compress if requested
            if compress:
                self.stdout.write(f'🗜️  Compressing backup...')
                zip_filename = f'db_backup_{timestamp}.zip'
                zip_path = os.path.join(output_dir, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(backup_path, backup_filename)
                
                # Remove uncompressed backup
                os.remove(backup_path)
                
                zip_size = os.path.getsize(zip_path)
                zip_size_mb = zip_size / (1024 * 1024)
                compression_ratio = (1 - zip_size / file_size) * 100
                
                self.stdout.write(self.style.SUCCESS(f'✅ Backup compressed!'))
                self.stdout.write(f'   File: {zip_path}')
                self.stdout.write(f'   Size: {zip_size_mb:.2f} MB')
                self.stdout.write(f'   Compression: {compression_ratio:.1f}%')

            # Cleanup old backups
            if keep_days > 0:
                self.stdout.write(f'🧹 Cleaning up old backups (keeping last {keep_days} days)...')
                deleted_count = self._cleanup_old_backups(output_dir, keep_days)
                if deleted_count > 0:
                    self.stdout.write(f'   Deleted {deleted_count} old backup(s)')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Backup failed: {str(e)}'))

    def _cleanup_old_backups(self, backup_dir, keep_days):
        """Delete backups older than keep_days"""
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0
        
        for filename in os.listdir(backup_dir):
            if not (filename.startswith('db_backup_') and (filename.endswith('.sqlite3') or filename.endswith('.zip'))):
                continue
            
            file_path = os.path.join(backup_dir, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if file_time < cutoff_time:
                os.remove(file_path)
                deleted_count += 1
                self.stdout.write(f'   Deleted: {filename}')
        
        return deleted_count
