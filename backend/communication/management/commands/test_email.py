"""
Management command to test email configuration
Usage: python manage.py test_email recipient@example.com
"""

from django.core.management.base import BaseCommand
from communication.email_utils import EmailSender


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            'recipient',
            type=str,
            help='Email address to send test message to'
        )
        parser.add_argument(
            '--template',
            type=str,
            default='announcement',
            help='Template to use for test email (default: announcement)'
        )

    def handle(self, *args, **options):
        recipient = options['recipient']
        template = options['template']

        self.stdout.write(self.style.SUCCESS(f'📧 Sending test email to: {recipient}'))
        self.stdout.write(f'   Using template: {template}')

        # Prepare test context based on template
        if template == 'announcement':
            context = {
                'title': 'Test Email',
                'message': 'This is a test email from the School Management System.\n\nIf you received this email, your SMTP configuration is working correctly.',
                'sender_name': 'System Administrator'
            }
            subject = 'Test Email - School Management System'
        
        elif template == 'fee_reminder':
            context = {
                'student_name': 'John Doe',
                'invoice_number': 'INV-202501-00001',
                'total_amount': 50000,
                'amount_paid': 20000,
                'balance': 30000,
                'due_date': '2025-01-31'
            }
            subject = 'Test Fee Reminder'
        
        else:
            self.stdout.write(self.style.ERROR(f'❌ Unknown template: {template}'))
            return

        # Send email
        try:
            success = EmailSender.send_email(
                subject=subject,
                to_emails=[recipient],
                template_name=template,
                context=context
            )

            if success:
                self.stdout.write(self.style.SUCCESS('✅ Test email sent successfully!'))
                self.stdout.write('   Check your inbox (and spam folder) for the test email.')
            else:
                self.stdout.write(self.style.ERROR('❌ Failed to send test email'))
                self.stdout.write('   Check your SMTP settings in settings.py')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            self.stdout.write('')
            self.stdout.write('Troubleshooting tips:')
            self.stdout.write('1. Verify EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS in settings.py')
            self.stdout.write('2. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct')
            self.stdout.write('3. For Gmail, use an App Password (not your regular password)')
            self.stdout.write('4. Ensure DEFAULT_FROM_EMAIL is set')
