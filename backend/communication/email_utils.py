"""
Email Configuration and Templates
Provides email sending functionality with customizable templates
"""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import os


class EmailSender:
    """Utility class for sending templated emails"""
    
    @staticmethod
    def send_email(subject, to_emails, template_name, context, from_email=None, attachments=None):
        """
        Send an email using a template
        
        Args:
            subject: Email subject
            to_emails: List of recipient emails
            template_name: Name of the template (without path)
            context: Dictionary of template variables
            from_email: Sender email (defaults to settings.DEFAULT_FROM_EMAIL)
            attachments: List of tuples (filename, content, mimetype)
        
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Use default from email if not provided
            from_email = from_email or settings.DEFAULT_FROM_EMAIL
            
            # Ensure to_emails is a list
            if isinstance(to_emails, str):
                to_emails = [to_emails]
            
            # Render HTML template
            html_content = render_to_string(f'emails/{template_name}.html', context)
            
            # Create plain text version
            text_content = strip_tags(html_content)
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=to_emails
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Add attachments if provided
            if attachments:
                for filename, content, mimetype in attachments:
                    email.attach(filename, content, mimetype)
            
            # Send
            email.send()
            return True
            
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False
    
    @staticmethod
    def send_fee_reminder(student, invoice):
        """Send fee payment reminder to parent/guardian"""
        context = {
            'student_name': student.user.get_full_name(),
            'invoice_number': invoice.invoice_number,
            'total_amount': invoice.total_amount,
            'amount_paid': invoice.amount_paid,
            'balance': invoice.total_amount - invoice.amount_paid,
            'due_date': invoice.due_date,
        }
        
        subject = f"Fee Payment Reminder - {student.user.get_full_name()}"
        to_emails = [student.guardian_email] if student.guardian_email else []
        
        if to_emails:
            return EmailSender.send_email(
                subject=subject,
                to_emails=to_emails,
                template_name='fee_reminder',
                context=context
            )
        return False

    @staticmethod
    def send_payment_reminder(recipient_email, context):
        """Send a grouped payment reminder for one parent/guardian."""
        if not recipient_email:
            return False

        subject = f"Fee Payment Reminder - {context.get('recipient_name', 'Parent/Guardian')}"
        return EmailSender.send_email(
            subject=subject,
            to_emails=[recipient_email],
            template_name='payment_reminder',
            context=context,
        )
    
    @staticmethod
    def send_payment_receipt(student, payment):
        """Send payment receipt via email"""
        context = {
            'student_name': student.user.get_full_name(),
            'receipt_number': payment.receipt_number,
            'payment_date': payment.payment_date,
            'amount': payment.amount,
            'payment_method': payment.get_payment_method_display(),
        }
        
        subject = f"Payment Receipt - {payment.receipt_number}"
        to_emails = [student.guardian_email] if student.guardian_email else []
        
        # Attach PDF receipt if generated
        attachments = []
        if hasattr(payment, 'receipt_pdf_path') and os.path.exists(payment.receipt_pdf_path):
            with open(payment.receipt_pdf_path, 'rb') as f:
                attachments.append((
                    f'{payment.receipt_number}.pdf',
                    f.read(),
                    'application/pdf'
                ))
        
        if to_emails:
            return EmailSender.send_email(
                subject=subject,
                to_emails=to_emails,
                template_name='payment_receipt',
                context=context,
                attachments=attachments if attachments else None
            )
        return False
    
    @staticmethod
    def send_report_card(student, academic_year, term):
        """Send report card to parent/guardian"""
        context = {
            'student_name': student.user.get_full_name(),
            'academic_year': academic_year.name,
            'term': term.get_term_number_display(),
            'class': str(student.current_class),
        }
        
        subject = f"Report Card - {student.user.get_full_name()} ({term})"
        to_emails = [student.guardian_email] if student.guardian_email else []
        
        if to_emails:
            return EmailSender.send_email(
                subject=subject,
                to_emails=to_emails,
                template_name='report_card',
                context=context
            )
        return False
    
    @staticmethod
    def send_announcement(recipients, title, message, sender_name='School Administration'):
        """Send general announcement to multiple recipients"""
        context = {
            'title': title,
            'message': message,
            'sender_name': sender_name,
        }
        
        return EmailSender.send_email(
            subject=title,
            to_emails=recipients,
            template_name='announcement',
            context=context
        )
    
    @staticmethod
    def send_absence_notification(student, attendance_record):
        """Notify parent of student absence"""
        context = {
            'student_name': student.user.get_full_name(),
            'date': attendance_record.date,
            'status': attendance_record.get_status_display(),
            'remarks': attendance_record.remarks or 'No remarks',
        }
        
        subject = f"Absence Notification - {student.user.get_full_name()}"
        to_emails = [student.guardian_email] if student.guardian_email else []
        
        if to_emails:
            return EmailSender.send_email(
                subject=subject,
                to_emails=to_emails,
                template_name='absence_notification',
                context=context
            )
        return False


class EmailTemplateManager:
    """Manage email templates in database"""
    
    TEMPLATE_TYPES = [
        ('fee_reminder', 'Fee Payment Reminder'),
        ('payment_reminder', 'Grouped Fee Payment Reminder'),
        ('payment_receipt', 'Payment Receipt'),
        ('report_card', 'Report Card'),
        ('announcement', 'General Announcement'),
        ('absence_notification', 'Absence Notification'),
        ('admission_confirmation', 'Admission Confirmation'),
        ('exam_schedule', 'Examination Schedule'),
    ]
    
    @staticmethod
    def get_template_variables(template_type):
        """Get available variables for each template type"""
        variables = {
            'fee_reminder': [
                '{{ student_name }}', '{{ invoice_number }}', '{{ total_amount }}',
                '{{ amount_paid }}', '{{ balance }}', '{{ due_date }}'
            ],
            'payment_reminder': [
                '{{ recipient_name }}', '{{ total_balance }}', '{{ earliest_due_date }}', '{{ children }}'
            ],
            'payment_receipt': [
                '{{ student_name }}', '{{ receipt_number }}', '{{ payment_date }}',
                '{{ amount }}', '{{ payment_method }}'
            ],
            'report_card': [
                '{{ student_name }}', '{{ academic_year }}', '{{ term }}', '{{ class }}'
            ],
            'announcement': [
                '{{ title }}', '{{ message }}', '{{ sender_name }}'
            ],
            'absence_notification': [
                '{{ student_name }}', '{{ date }}', '{{ status }}', '{{ remarks }}'
            ],
        }
        return variables.get(template_type, [])
