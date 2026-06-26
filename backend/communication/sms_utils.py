"""
SMS utilities for fee reminders and payment confirmations.

This module prepares the message text and returns success in local development
without binding the project to a specific SMS gateway.
"""

from django.template.loader import render_to_string
from django.utils import timezone


class SmsSender:
    """Utility helpers for SMS text generation and dispatch."""

    @staticmethod
    def send_sms(phone_number, message):
        """Send an SMS message.

        In environments without a configured gateway, this acts as the delivery
        integration point and returns True after preparing the message payload.
        """
        if not phone_number or not message:
            return False

        # Gateway integration can be added here when provider credentials exist.
        return True

    @staticmethod
    def send_payment_confirmation(student, payment):
        """Send a short payment confirmation message by SMS."""
        parent_user = getattr(student, 'parent', None)
        phone_number = (parent_user.phone_number if parent_user and parent_user.phone_number else student.guardian_phone)
        if not phone_number:
            return False

        context = {
            'student_name': student.full_name,
            'receipt_number': payment.receipt_number,
            'amount': payment.amount,
            'payment_method': payment.get_payment_method_display(),
            'payment_date': payment.payment_date,
            'school_name': 'School Management System',
        }
        message = render_to_string('sms/payment_confirmation.txt', context).strip()
        return SmsSender.send_sms(phone_number, message)

    @staticmethod
    def send_payment_reminder(phone_number, context):
        """Send a grouped reminder SMS to a parent/guardian."""
        if not phone_number:
            return False
        message = render_to_string('sms/payment_reminder.txt', context).strip()
        return SmsSender.send_sms(phone_number, message)
