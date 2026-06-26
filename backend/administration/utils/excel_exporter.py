"""
Excel Export Utilities
Export various data to formatted Excel files
"""

from openpyxl import Workbook
from openpyxl.styles import Font, Fill, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import os
from django.conf import settings
from openpyxl.worksheet.worksheet import Worksheet


class ExcelExporter:
    """Base class for Excel exports with formatting"""
    
    def __init__(self):
        self.workbook = Workbook()
        self.worksheet: Worksheet = self.workbook.active if self.workbook.active is not None else self.workbook.create_sheet(title='Sheet1')
        
        # Define styles
        self.header_font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
        self.header_fill = PatternFill(start_color='0d6efd', end_color='0d6efd', fill_type='solid')
        self.header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        self.data_font = Font(name='Arial', size=10)
        self.data_alignment = Alignment(horizontal='left', vertical='center')
        
        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    def style_header_row(self, row_num=1):
        """Apply styling to header row"""
        worksheet = self.worksheet
        for cell in worksheet[row_num]:
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
    
    def auto_adjust_columns(self):
        """Auto-adjust column widths based on content"""
        worksheet = self.worksheet
        for column_index, column in enumerate(worksheet.iter_cols(), start=1):
            max_length = 0
            column_letter = get_column_letter(column_index)
            
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def add_filters(self, start_row=1, end_row=None, end_column=None):
        """Add auto-filter to data"""
        worksheet = self.worksheet
        if end_row is None:
            end_row = worksheet.max_row
        if end_column is None:
            end_column = worksheet.max_column
        
        end_col_letter = get_column_letter(end_column)
        worksheet.auto_filter.ref = f'A{start_row}:{end_col_letter}{end_row}'
    
    def save(self, filename):
        """Save workbook to file"""
        self.workbook.save(filename)
        return filename


class StudentExporter(ExcelExporter):
    """Export student data to Excel"""
    
    def export(self, students, include_class=True, include_contact=True):
        """Export students to Excel"""
        
        self.worksheet.title = 'Students'
        self._write_students_to_sheet(students, self.worksheet, include_class, include_contact)
        return self.workbook
    
    def _write_students_to_sheet(self, students, worksheet, include_class=True, include_contact=True):
        """Write student data to a worksheet"""
        
        # Headers
        headers = ['Admission No', 'First Name', 'Last Name', 'Gender', 'Date of Birth']
        
        if include_class:
            headers.extend(['Class', 'Grade'])
        
        if include_contact:
            headers.extend(['Phone', 'Email', 'Address'])
        
        headers.extend(['Nationality', 'Religion', 'Blood Group'])
        
        # Write headers
        worksheet.append(headers)
        
        # Style headers
        for cell in worksheet[1]:
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        # Write data
        for student in students:
            row = [
                student.admission_number or 'N/A',
                student.user.first_name,
                student.user.last_name,
                student.get_gender_display(),
                student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else 'N/A',
            ]
            
            if include_class:
                row.extend([
                    str(student.current_class) if student.current_class else 'N/A',
                    str(student.current_class.grade) if student.current_class and student.current_class.grade else 'N/A',
                ])
            
            if include_contact:
                row.extend([
                    student.phone_number or 'N/A',
                    student.user.email or 'N/A',
                    student.address or 'N/A',
                ])
            
            row.extend([
                student.nationality or 'N/A',
                student.religion or 'N/A',
                student.blood_group or 'N/A',
            ])
            
            worksheet.append(row)
        
        # Apply formatting
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Add filters
        end_col_letter = get_column_letter(worksheet.max_column)
        worksheet.auto_filter.ref = f'A1:{end_col_letter}{worksheet.max_row}'


class FeeReportExporter(ExcelExporter):
    """Export fee collection reports to Excel"""
    
    def export(self, invoices, include_payments=True):
        """Export fee invoices and payments"""
        
        self.worksheet.title = 'Fee Report'
        self._write_fees_to_sheet(invoices, self.worksheet, include_payments)
        return self.workbook
    
    def _write_fees_to_sheet(self, invoices, worksheet, include_payments=True):
        """Write fee data to a worksheet"""
        
        # Headers
        headers = [
            'Invoice No', 'Student Name', 'Admission No', 'Class',
            'Invoice Date', 'Due Date', 'Total Amount', 'Amount Paid',
            'Balance', 'Status'
        ]
        
        if include_payments:
            headers.extend(['Last Payment Date', 'Last Payment Amount'])
        
        # Write headers
        worksheet.append(headers)
        
        # Style headers
        for cell in worksheet[1]:
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        # Write data
        for invoice in invoices:
            balance = invoice.total_amount - invoice.amount_paid
            
            row = [
                invoice.invoice_number,
                invoice.student.user.get_full_name(),
                invoice.student.admission_number or 'N/A',
                str(invoice.student.current_class) if invoice.student.current_class else 'N/A',
                invoice.billing_date.strftime('%Y-%m-%d'),
                invoice.due_date.strftime('%Y-%m-%d'),
                float(invoice.total_amount),
                float(invoice.amount_paid),
                float(balance),
                invoice.get_status_display(),
            ]
            
            if include_payments:
                last_payment = invoice.payment_set.order_by('-payment_date').first()
                if last_payment:
                    row.extend([
                        last_payment.payment_date.strftime('%Y-%m-%d'),
                        float(last_payment.amount),
                    ])
                else:
                    row.extend(['N/A', 0.00])
            
            worksheet.append(row)
        
        # Format currency columns
        for row in range(2, worksheet.max_row + 1):
            for col in [7, 8, 9]:  # Amount columns
                cell = worksheet.cell(row=row, column=col)
                cell.number_format = '₦#,##0.00'
            
            if include_payments:
                cell = worksheet.cell(row=row, column=12)
                cell.number_format = '₦#,##0.00'
        
        # Apply formatting
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Add filters
        end_col_letter = get_column_letter(worksheet.max_column)
        worksheet.auto_filter.ref = f'A1:{end_col_letter}{worksheet.max_row}'
        
        # Add summary at bottom
        summary_row = worksheet.max_row + 2
        worksheet.cell(row=summary_row, column=1, value='SUMMARY')
        worksheet.cell(row=summary_row, column=1).font = Font(bold=True, size=12)
        
        total_invoiced = sum(float(inv.total_amount) for inv in invoices)
        total_paid = sum(float(inv.amount_paid) for inv in invoices)
        total_balance = total_invoiced - total_paid
        
        worksheet.cell(row=summary_row + 1, column=1, value='Total Invoiced:')
        worksheet.cell(row=summary_row + 1, column=2, value=total_invoiced).number_format = '₦#,##0.00'
        
        worksheet.cell(row=summary_row + 2, column=1, value='Total Paid:')
        worksheet.cell(row=summary_row + 2, column=2, value=total_paid).number_format = '₦#,##0.00'
        
        worksheet.cell(row=summary_row + 3, column=1, value='Total Balance:')
        worksheet.cell(row=summary_row + 3, column=2, value=total_balance).number_format = '₦#,##0.00'


class AttendanceExporter(ExcelExporter):
    """Export attendance records to Excel"""
    
    def export(self, attendance_records, group_by_date=True):
        """Export attendance data"""
        
        self.worksheet.title = 'Attendance'
        self._write_attendance_to_sheet(attendance_records, self.worksheet)
        return self.workbook
    
    def _write_attendance_to_sheet(self, attendance_records, worksheet):
        """Write attendance data to a worksheet"""
        
        # Headers
        headers = ['Date', 'Student Name', 'Admission No', 'Class', 'Status', 'Remarks']
        
        # Write headers
        worksheet.append(headers)
        
        # Style headers
        for cell in worksheet[1]:
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.thin_border
        
        # Write data
        for record in attendance_records:
            row = [
                record.date.strftime('%Y-%m-%d'),
                record.student.user.get_full_name(),
                record.student.admission_number or 'N/A',
                str(record.student.current_class) if record.student.current_class else 'N/A',
                record.get_status_display(),
                record.remarks or '',
            ]
            
            worksheet.append(row)
        
        # Apply formatting
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        # Add filters
        end_col_letter = get_column_letter(worksheet.max_column)
        worksheet.auto_filter.ref = f'A1:{end_col_letter}{worksheet.max_row}'
        
        # Add summary
        summary_row = worksheet.max_row + 2
        worksheet.cell(row=summary_row, column=1, value='SUMMARY')
        worksheet.cell(row=summary_row, column=1).font = Font(bold=True, size=12)
        
        total_records = len(attendance_records)
        present_count = sum(1 for r in attendance_records if r.status == 'present')
        absent_count = sum(1 for r in attendance_records if r.status == 'absent')
        
        worksheet.cell(row=summary_row + 1, column=1, value='Total Records:')
        worksheet.cell(row=summary_row + 1, column=2, value=total_records)
        
        worksheet.cell(row=summary_row + 2, column=1, value='Present:')
        worksheet.cell(row=summary_row + 2, column=2, value=present_count)
        
        worksheet.cell(row=summary_row + 3, column=1, value='Absent:')
        worksheet.cell(row=summary_row + 3, column=2, value=absent_count)
        
        if total_records > 0:
            attendance_rate = (present_count / total_records) * 100
            worksheet.cell(row=summary_row + 4, column=1, value='Attendance Rate:')
            worksheet.cell(row=summary_row + 4, column=2, value=f'{attendance_rate:.1f}%')


def export_students_to_excel(students, output_path=None):
    """Export students to Excel file"""
    if output_path is None:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(output_dir, exist_ok=True)
        filename = f'students_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        output_path = os.path.join(output_dir, filename)
    
    exporter = StudentExporter()
    exporter.export(students)
    exporter.save(output_path)
    
    return output_path


def export_fees_to_excel(invoices, output_path=None):
    """Export fee report to Excel file"""
    if output_path is None:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(output_dir, exist_ok=True)
        filename = f'fee_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        output_path = os.path.join(output_dir, filename)
    
    exporter = FeeReportExporter()
    exporter.export(invoices)
    exporter.save(output_path)
    
    return output_path


def export_attendance_to_excel(attendance_records, output_path=None):
    """Export attendance to Excel file"""
    if output_path is None:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'exports')
        os.makedirs(output_dir, exist_ok=True)
        filename = f'attendance_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        output_path = os.path.join(output_dir, filename)
    
    exporter = AttendanceExporter()
    exporter.export(attendance_records)
    exporter.save(output_path)
    
    return output_path
