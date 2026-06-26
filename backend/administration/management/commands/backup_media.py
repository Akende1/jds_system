"""
Management command to backup media files
Usage: python manage.py backup_media [--output-dir DIR]
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import zipfile
from datetime import datetime


class Command(BaseCommand):
    help = 'Create a backup of media files (uploads, receipts, exports, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Directory to store backup (default: media/backups/media)'
        )
        parser.add_argument(
            '--keep-days',
            type=int,
            default=30,
            help='Number of days to keep old backups (default: 30)'
        )
        parser.add_argument(
            '--include-dirs',
            type=str,
            help='Comma-separated list of subdirectories to include (default: all)'
        )

    def handle(self, *args, **options):
        output_dir = options.get('output_dir')
        keep_days = options.get('keep_days')
        include_dirs = options.get('include_dirs')

        self.stdout.write(self.style.SUCCESS('📁 Starting media files backup...'))

        # Get media root
        media_root = settings.MEDIA_ROOT
        
        if not os.path.exists(media_root):
            self.stdout.write(self.style.ERROR(f'❌ Media directory not found: {media_root}'))
            return

        # Setup backup directory
        if output_dir is None:
            output_dir = os.path.join(media_root, 'backups', 'media')
        
        os.makedirs(output_dir, exist_ok=True)

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'media_backup_{timestamp}.zip'
        zip_path = os.path.join(output_dir, zip_filename)

        try:
            # Determine which directories to include
            if include_dirs:
                dirs_to_backup = [d.strip() for d in include_dirs.split(',')]
            else:
                # Backup all except backups directory
                dirs_to_backup = [
                    d for d in os.listdir(media_root) 
                    if os.path.isdir(os.path.join(media_root, d)) and d != 'backups'
                ]

            self.stdout.write(f'📦 Creating ZIP archive...')
            file_count = 0
            total_size = 0

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for dir_name in dirs_to_backup:
                    dir_path = os.path.join(media_root, dir_name)
                    
                    if not os.path.exists(dir_path):
                        self.stdout.write(self.style.WARNING(f'   ⚠️  Directory not found: {dir_name}'))
                        continue
                    
                    self.stdout.write(f'   Adding: {dir_name}/')
                    
                    # Walk through directory
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Get relative path for ZIP
                            arcname = os.path.relpath(file_path, media_root)
                            zipf.write(file_path, arcname)
                            file_count += 1
                            total_size += os.path.getsize(file_path)

            # Get final ZIP size
            zip_size = os.path.getsize(zip_path)
            zip_size_mb = zip_size / (1024 * 1024)
            total_size_mb = total_size / (1024 * 1024)
            compression_ratio = (1 - zip_size / total_size) * 100 if total_size > 0 else 0

            self.stdout.write(self.style.SUCCESS('✅ Media files backed up successfully!'))
            self.stdout.write(f'   File: {zip_path}')
            self.stdout.write(f'   Files: {file_count}')
            self.stdout.write(f'   Original size: {total_size_mb:.2f} MB')
            self.stdout.write(f'   Compressed size: {zip_size_mb:.2f} MB')
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
            if not (filename.startswith('media_backup_') and filename.endswith('.zip')):
                continue
            
            file_path = os.path.join(backup_dir, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if file_time < cutoff_time:
                os.remove(file_path)
                deleted_count += 1
                self.stdout.write(f'   Deleted: {filename}')
        
        return deleted_count
