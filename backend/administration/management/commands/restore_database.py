"""
Management command to restore database from backup
Usage: python manage.py restore_database <backup_file>
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
import zipfile


class Command(BaseCommand):
    help = 'Restore database from a backup file'

    def add_arguments(self, parser):
        parser.add_argument(
            'backup_file',
            type=str,
            help='Path to backup file (.sqlite3 or .zip)'
        )
        parser.add_argument(
            '--no-backup',
            action='store_true',
            help='Skip creating backup of current database before restore'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        backup_file = options['backup_file']
        no_backup = options.get('no_backup', False)
        force = options.get('force', False)

        self.stdout.write(self.style.WARNING('⚠️  DATABASE RESTORE'))
        self.stdout.write(self.style.WARNING('This will replace your current database!'))

        # Verify backup file exists
        if not os.path.exists(backup_file):
            self.stdout.write(self.style.ERROR(f'❌ Backup file not found: {backup_file}'))
            return

        # Get current database path
        db_path = settings.DATABASES['default']['NAME']

        # Show info
        self.stdout.write('')
        self.stdout.write(f'Backup file: {backup_file}')
        self.stdout.write(f'Current DB:  {db_path}')
        self.stdout.write('')

        # Confirmation
        if not force:
            confirm = input('Are you sure you want to restore? This cannot be undone. (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Restore cancelled.'))
                return

        try:
            # Backup current database first
            if not no_backup and os.path.exists(db_path):
                self.stdout.write('💾 Creating backup of current database...')
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                current_backup = f'{db_path}.before_restore_{timestamp}'
                shutil.copy2(db_path, current_backup)
                self.stdout.write(f'   Saved to: {current_backup}')

            # Handle ZIP files
            restore_file = backup_file
            if backup_file.endswith('.zip'):
                self.stdout.write('📦 Extracting ZIP archive...')
                temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_restore')
                os.makedirs(temp_dir, exist_ok=True)
                
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    # Extract all files
                    zipf.extractall(temp_dir)
                    
                    # Find the .sqlite3 file
                    sqlite_files = [f for f in os.listdir(temp_dir) if f.endswith('.sqlite3')]
                    
                    if not sqlite_files:
                        self.stdout.write(self.style.ERROR('❌ No .sqlite3 file found in ZIP'))
                        shutil.rmtree(temp_dir)
                        return
                    
                    restore_file = os.path.join(temp_dir, sqlite_files[0])
                    self.stdout.write(f'   Found: {sqlite_files[0]}')

            # Restore database
            self.stdout.write('🔄 Restoring database...')
            shutil.copy2(restore_file, db_path)

            # Cleanup temp files
            if backup_file.endswith('.zip'):
                shutil.rmtree(temp_dir)

            # Verify restore
            if os.path.exists(db_path):
                file_size = os.path.getsize(db_path) / (1024 * 1024)
                self.stdout.write(self.style.SUCCESS('✅ Database restored successfully!'))
                self.stdout.write(f'   Database size: {file_size:.2f} MB')
                self.stdout.write('')
                self.stdout.write(self.style.WARNING('⚠️  Important: Restart the Django development server for changes to take effect'))
            else:
                self.stdout.write(self.style.ERROR('❌ Restore verification failed'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Restore failed: {str(e)}'))
            
            # Attempt to restore from pre-restore backup
            if not no_backup and 'current_backup' in locals():
                self.stdout.write('🔄 Attempting to restore previous database...')
                try:
                    shutil.copy2(current_backup, db_path)
                    self.stdout.write(self.style.SUCCESS('✅ Previous database restored'))
                except:
                    self.stdout.write(self.style.ERROR('❌ Could not restore previous database'))
