"""
PDF Receipt Generation Utilities
Generates professional payment receipts with school letterhead
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from datetime import datetime
from decimal import Decimal
import os
from django.conf import settings


class ReceiptPDFGenerator:
    """Generate professional PDF receipts for payments"""
    
    def __init__(self, payment):
        self.payment = payment
        self.student = payment.student
        self.invoice = payment.invoice
        self.school = self.get_school_info()
        
    def get_school_info(self):
        """Get school information"""
        from administration.models import SchoolProfile
        try:
            return SchoolProfile.objects.first()
        except:
            return None
    
    def generate(self, file_path):
        """Generate the PDF receipt"""
        doc = SimpleDocTemplate(
            file_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0d6efd'),
            spaceAfter=30,
            alignment=1,  # Center
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#212529'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        )
        
        # School Header
        if self.school:
            school_name = Paragraph(
                f"<b>{self.school.name}</b>",
                title_style
            )
            elements.append(school_name)
            
            if self.school.address:
                address = Paragraph(
                    f"{self.school.address}<br/>"
                    f"Phone: {self.school.phone_number or 'N/A'} | "
                    f"Email: {self.school.email or 'N/A'}",
                    styles['Normal']
                )
                elements.append(address)
        
        elements.append(Spacer(1, 20))
        
        # Receipt Title
        receipt_title = Paragraph("<b>PAYMENT RECEIPT</b>", heading_style)
        elements.append(receipt_title)
        elements.append(Spacer(1, 20))
        
        # Receipt Details Table
        receipt_data = [
            ['Receipt Number:', self.payment.receipt_number],
            ['Date:', self.payment.payment_date.strftime('%B %d, %Y')],
            ['Payment Method:', self.payment.get_payment_method_display()],
        ]
        
        if self.payment.transaction_id:
            receipt_data.append(['Transaction ID:', self.payment.transaction_id])
        
        receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
        receipt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6c757d')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(receipt_table)
        elements.append(Spacer(1, 20))
        
        # Student Information
        student_heading = Paragraph("<b>Student Information</b>", heading_style)
        elements.append(student_heading)
        
        student_data = [
            ['Student Name:', self.student.user.get_full_name()],
            ['Admission Number:', self.student.admission_number or 'N/A'],
            ['Class:', str(self.student.current_class) if self.student.current_class else 'N/A'],
        ]
        
        student_table = Table(student_data, colWidths=[2*inch, 4*inch])
        student_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#6c757d')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(student_table)
        elements.append(Spacer(1, 20))
        
        # Payment Details
        payment_heading = Paragraph("<b>Payment Details</b>", heading_style)
        elements.append(payment_heading)
        
        # Payment breakdown table
        payment_breakdown = [
            ['Description', 'Amount'],
            [f'Invoice #{self.invoice.invoice_number}', f'₦{self.invoice.total_amount:,.2f}'],
            ['Previous Payments', f'₦{self.invoice.amount_paid - self.payment.amount:,.2f}'],
            ['Current Payment', f'₦{self.payment.amount:,.2f}'],
            ['Balance Due', f'₦{self.invoice.total_amount - self.invoice.amount_paid:,.2f}'],
        ]
        
        payment_table = Table(payment_breakdown, colWidths=[4*inch, 2*inch])
        payment_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            
            # Highlight current payment
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor('#d1ecf1')),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            
            # Highlight balance
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 30))
        
        # Payment amount in words
        amount_words = self.number_to_words(self.payment.amount)
        amount_text = Paragraph(
            f"<b>Amount in Words:</b> {amount_words.title()} Naira Only",
            styles['Normal']
        )
        elements.append(amount_text)
        elements.append(Spacer(1, 30))
        
        # Footer
        footer_data = [
            ['_'*25, '_'*25],
            ['Received By', 'Authorized Signature'],
        ]
        
        footer_table = Table(footer_data, colWidths=[3*inch, 3*inch])
        footer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, 1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 1), (-1, 1), 10),
        ]))
        elements.append(footer_table)
        elements.append(Spacer(1, 20))
        
        # Note
        note = Paragraph(
            "<i>This is a computer-generated receipt and does not require a signature. "
            "Please keep this receipt for your records.</i>",
            styles['Normal']
        )
        elements.append(note)
        
        # Build PDF
        doc.build(elements)
        
        return file_path
    
    def number_to_words(self, number):
        """Convert number to words (simplified for Nigerian Naira)"""
        number = int(number)
        
        ones = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
        tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
        teens = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 
                 'sixteen', 'seventeen', 'eighteen', 'nineteen']
        
        if number == 0:
            return 'zero'
        
        if number < 10:
            return ones[number]
        elif number < 20:
            return teens[number - 10]
        elif number < 100:
            return tens[number // 10] + (' ' + ones[number % 10] if number % 10 != 0 else '')
        elif number < 1000:
            return ones[number // 100] + ' hundred' + (' and ' + self.number_to_words(number % 100) if number % 100 != 0 else '')
        elif number < 1000000:
            return self.number_to_words(number // 1000) + ' thousand' + (' ' + self.number_to_words(number % 1000) if number % 1000 != 0 else '')
        else:
            return self.number_to_words(number // 1000000) + ' million' + (' ' + self.number_to_words(number % 1000000) if number % 1000000 != 0 else '')


def generate_receipt_pdf(payment, output_dir=None):
    """
    Generate PDF receipt for a payment
    
    Args:
        payment: Payment object
        output_dir: Directory to save PDF (defaults to media/receipts/)
    
    Returns:
        file_path: Path to generated PDF
    """
    if output_dir is None:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename
    filename = f'{payment.receipt_number}.pdf'
    file_path = os.path.join(output_dir, filename)
    
    # Generate PDF
    generator = ReceiptPDFGenerator(payment)
    generator.generate(file_path)
    
    return file_path
