"""
Finance management views for frontend
Real-time payment recording, receipt generation, account management"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import date, datetime, timedelta
from decimal import Decimal
from administration.decorators import bursar_or_manager, staff_only
from finance.models import FeeInvoice, Payment, FeeStructure, Expense, PaymentReminder
from administration.models import Student, AcademicYear, Term, Grade
from finance.utils.receipt_generator import ReceiptPDFGenerator


def _generate_receipt_pdf(payment) -> str:
    """Generate receipt PDF using the available ReceiptPDFGenerator API."""
    generator = ReceiptPDFGenerator(payment)

    generate_pdf = getattr(generator, 'generate_pdf', None)
    if callable(generate_pdf):
        result = generate_pdf()
        if result:
            return str(result)

    build_pdf = getattr(generator, 'build_pdf', None)
    if callable(build_pdf):
        result = build_pdf()
        if result:
            return str(result)

    create_pdf = getattr(generator, 'create_pdf', None)
    if callable(create_pdf):
        result = create_pdf()
        if result:
            return str(result)

    raise AttributeError('ReceiptPDFGenerator has no supported PDF generation method.')


def _format_currency(amount) -> str:
    return f'K {Decimal(str(amount or 0)):.2f}'


def _build_parent_balance_groups(invoices):
    groups = {}

    for invoice in invoices:
        student = invoice.student
        parent_user = getattr(student, 'parent', None)

        if parent_user:
            group_key = f'parent:{parent_user.id}'
            recipient_name = parent_user.get_full_name() or parent_user.username or student.guardian_name
            email_address = parent_user.email or student.guardian_email
            phone_number = parent_user.phone_number or student.guardian_phone
        else:
            contact_key = student.guardian_email or student.guardian_phone or student.admission_number
            group_key = f'guardian:{contact_key}'
            recipient_name = student.guardian_name or student.full_name
            email_address = student.guardian_email
            phone_number = student.guardian_phone

        group = groups.setdefault(
            group_key,
            {
                'recipient_name': recipient_name,
                'email_address': email_address,
                'phone_number': phone_number,
                'children': [],
                'total_balance': Decimal('0.00'),
                'earliest_due_date': invoice.due_date,
            },
        )

        class_name = ''
        if student.current_class:
            class_name = getattr(student.current_class, 'name', '') or str(student.current_class)

        group['children'].append(
            {
                'student_id': student.id,
                'student_name': student.full_name,
                'admission_number': student.admission_number,
                'class_name': class_name,
                'invoice_number': invoice.invoice_number,
                'balance': Decimal(str(invoice.balance)),
                'due_date': invoice.due_date,
            }
        )
        group['total_balance'] += Decimal(str(invoice.balance))
        if invoice.due_date and (group['earliest_due_date'] is None or invoice.due_date < group['earliest_due_date']):
            group['earliest_due_date'] = invoice.due_date

    return list(groups.values())


def _build_reminder_context(group, reminder_type):
    return {
        'recipient_name': group['recipient_name'],
        'children': group['children'],
        'total_balance': group['total_balance'],
        'earliest_due_date': group['earliest_due_date'],
        'reminder_type': reminder_type,
        'school_name': 'School Management System',
    }


@staff_only
def invoice_list(request):
    """List all invoices with filters"""
    invoices = FeeInvoice.objects.select_related(
        'student', 'academic_year', 'term'
    ).all()
    
    # Filters
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    class_filter = request.GET.get('class', '')
    
    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__admission_number__icontains=search)
        )
    
    if status_filter:
        if status_filter == 'paid':
            invoices = invoices.filter(balance=0)
        elif status_filter == 'partial':
            invoices = invoices.filter(balance__gt=0, amount_paid__gt=0)
        elif status_filter == 'unpaid':
            invoices = invoices.filter(amount_paid=0)
        elif status_filter == 'overdue':
            invoices = invoices.filter(due_date__lt=date.today(), balance__gt=0)
    
    if class_filter:
        invoices = invoices.filter(student__current_class_id=class_filter)
    
    # Summary stats
    total_invoiced = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = invoices.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    total_outstanding = invoices.aggregate(Sum('balance'))['balance__sum'] or 0
    
    # Pagination
    paginator = Paginator(invoices, 50)
    page = request.GET.get('page', 1)
    invoices_page = paginator.get_page(page)
    
    context = {
        'invoices': invoices_page,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'total_outstanding': total_outstanding,
        'search': search,
        'status_filter': status_filter,
    }
    
    return render(request, 'frontend/finance/invoice_list.html', context)


@bursar_or_manager
def fee_structure_list(request):
    """List all defined fee structures"""
    structures = FeeStructure.objects.select_related('grade', 'academic_year').all()
    return render(request, 'frontend/finance/fee_structure_list.html', {'structures': structures})


@bursar_or_manager
def fee_structure_add(request):
    """Create a new fee structure for a grade/term"""
    if request.method == 'POST':
        try:
            grade_id = request.POST.get('grade') or None
            year_id = request.POST.get('academic_year')
            name = request.POST.get('name')
            fee_type = request.POST.get('fee_type', 'tuition')
            amount = request.POST.get('amount')
            payment_frequency = request.POST.get('payment_frequency', 'term')
            is_compulsory = request.POST.get('is_compulsory') == 'on'
            description = request.POST.get('description', '')
            
            FeeStructure.objects.create(
                grade_id=grade_id,
                academic_year_id=year_id,
                name=name,
                fee_type=fee_type,
                amount=Decimal(amount or 0),
                payment_frequency=payment_frequency,
                is_compulsory=is_compulsory,
                description=description,
                is_active=True,
            )
            messages.success(request, 'Fee structure created successfully!')
            return redirect('frontend:fee_structure_list')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            
    context = {
        'grades': Grade.objects.all(),
        'years': AcademicYear.objects.all(),
        'fee_types': FeeStructure.FEE_TYPE_CHOICES,
        'payment_frequencies': FeeStructure.PAYMENT_FREQUENCY_CHOICES,
    }
    return render(request, 'frontend/finance/fee_structure_add.html', context)


@bursar_or_manager
def invoice_generate(request):
    """Generate invoices (bulk or individual)"""
    if request.method == 'POST':
        generation_type = request.POST.get('type')  # 'bulk' or 'individual'
        
        try:
            current_year = AcademicYear.objects.filter(is_current=True).first()
            current_term = Term.objects.filter(academic_year=current_year, is_current=True).first()
            
            if generation_type == 'bulk':
                grade_id = request.POST.get('grade')
                class_id = request.POST.get('class')
                
                # Get students
                students = Student.objects.filter(status='active')
                if class_id:
                    students = students.filter(current_class_id=class_id)
                elif grade_id:
                    students = students.filter(current_class__grade_id=grade_id)
                
                # Get fee structure
                fee_structures = FeeStructure.objects.filter(academic_year=current_year)
                if grade_id:
                    fee_structures = fee_structures.filter(grade_id=grade_id)
                fee_structure = fee_structures.first()
                
                if not fee_structure:
                    messages.error(request, 'No fee structure found for the selected academic year')
                    return redirect('frontend:invoice_generate')
                
                # Resolve fee amount safely (supports different FeeStructure schemas)
                raw_total_amount = getattr(fee_structure, 'total_amount', None)
                if raw_total_amount is None:
                    raw_total_amount = getattr(fee_structure, 'amount', None)
                get_total_amount = getattr(fee_structure, 'get_total_amount', None)
                if raw_total_amount is None and callable(get_total_amount):
                    raw_total_amount = get_total_amount()
                invoice_total_amount = Decimal(str(raw_total_amount or 0))

                # Resolve due date safely (supports different FeeStructure schemas)
                invoice_due_date = getattr(fee_structure, 'due_date', None)
                if invoice_due_date is None:
                    invoice_due_date = getattr(fee_structure, 'payment_deadline', None)
                if invoice_due_date is None and current_term is not None:
                    invoice_due_date = getattr(current_term, 'end_date', None)
                if invoice_due_date is None:
                    invoice_due_date = date.today()
                
                # Generate invoices
                count = 0
                for student in students:
                    # Check if invoice already exists
                    existing = FeeInvoice.objects.filter(
                        student=student,
                        academic_year=current_year,
                        term=current_term
                    ).exists()
                    
                    if not existing:
                        # Generate invoice number
                        last_invoice = FeeInvoice.objects.order_by('-invoice_number').first()
                        if last_invoice and last_invoice.invoice_number:
                            last_num = int(last_invoice.invoice_number.split('-')[-1])
                            invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-{str(last_num + 1).zfill(5)}"
                        else:
                            invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-00001"
                        
                        FeeInvoice.objects.create(
                            invoice_number=invoice_number,
                            student=student,
                            academic_year=current_year,
                            term=current_term,
                            total_amount=invoice_total_amount,
                            amount_paid=0,
                            balance=invoice_total_amount,
                            due_date=invoice_due_date,
                            status='pending')
                        # Changed from 'enrolled' to 'active'
                        count += 1
                
                messages.success(request, f'{count} invoices generated successfully!')
            
            else:  # individual
                student_id = request.POST.get('student')
                amount = float(request.POST.get('amount'))
                due_date = request.POST.get('due_date')
                
                student = Student.objects.get(id=student_id)
                
                # Generate invoice number
                last_invoice = FeeInvoice.objects.order_by('-invoice_number').first()
                if last_invoice and last_invoice.invoice_number:
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                    invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-{str(last_num + 1).zfill(5)}"
                else:
                    invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-00001"
                
                FeeInvoice.objects.create(
                    invoice_number=invoice_number,
                    student=student,
                    academic_year=current_year,
                    term=current_term,
                    total_amount=amount,
                    amount_paid=0,
                    balance=amount,
                    due_date=due_date,
                    status='pending'
                )
                
                messages.success(request, 'Invoice generated successfully!')
            
            return redirect('frontend:invoice_list')
        
        except Exception as e:
            messages.error(request, f'Error generating invoice: {str(e)}')
    
    # GET request
    from administration.models import Grade, ClassRoom
    grades = Grade.objects.all()
    classes = ClassRoom.objects.select_related('grade').all()
    students = Student.objects.filter(status='active')
    
    context = {
        'grades': grades,
        'classes': classes,
        'students': students,
    }
    
    return render(request, 'frontend/finance/invoice_generate.html', context)


@staff_only
def invoice_detail(request, pk):
    """Invoice detail page"""
    invoice = get_object_or_404(
        FeeInvoice.objects.select_related('student', 'academic_year', 'term'),
        pk=pk
    )
    
    # Payment history
    payments = Payment.objects.filter(invoice=invoice).order_by('-payment_date')
    
    context = {
        'invoice': invoice,
        'payments': payments,
    }
    
    return render(request, 'frontend/finance/invoice_detail.html', context)


@bursar_or_manager
def payment_record(request):
    """Record a new payment"""
    if request.method == 'POST':
        try:
            invoice_id = request.POST.get('invoice_id')
            amount = float(request.POST.get('amount'))
            payment_method = request.POST.get('payment_method')
            reference_number = request.POST.get('reference_number', '')
            notes = request.POST.get('notes', '').strip()
            send_receipt_email = request.POST.get('send_receipt_email') == 'on'
            send_confirmation_sms = request.POST.get('send_confirmation_sms') == 'on'
            payment_date_value = request.POST.get('payment_date')
            
            invoice = FeeInvoice.objects.get(id=invoice_id)
            student = invoice.student

            if payment_date_value:
                payment_date = timezone.make_aware(datetime.strptime(payment_date_value, '%Y-%m-%d'))
            else:
                payment_date = timezone.now()
            
            # Validate amount
            if Decimal(amount) > invoice.balance:
                messages.error(request, 'Payment amount exceeds outstanding balance')
                return redirect('frontend:payment_record')
            
            # Generate receipt number
            last_payment = Payment.objects.order_by('-receipt_number').first()
            if last_payment and last_payment.receipt_number:
                last_num = int(last_payment.receipt_number.split('-')[-1])
                receipt_number = f"REC-{datetime.now().strftime('%Y%m')}-{str(last_num + 1).zfill(5)}"
            else:
                receipt_number = f"REC-{datetime.now().strftime('%Y%m')}-00001"
            
            # Create payment
            payment = Payment.objects.create(
                receipt_number=receipt_number,
                student=student,
                invoice=invoice,
                amount=Decimal(amount),
                payment_date=payment_date,
                payment_method=payment_method,
                payment_status='confirmed',
                reference_number=reference_number,
                remarks=notes,
                received_by=request.user.get_full_name() or request.user.username,
            )
            
            # Generate PDF receipt
            _ = _generate_receipt_pdf(payment)

            from communication.email_utils import EmailSender
            from communication.sms_utils import SmsSender

            if send_receipt_email:
                EmailSender.send_payment_receipt(student, payment)

            if send_confirmation_sms:
                SmsSender.send_payment_confirmation(student, payment)
            
            messages.success(request, f'Payment recorded successfully! Receipt: {receipt_number}')
            return redirect('frontend:payment_receipt', pk=payment.pk)
        
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
    
    # GET request - show form with pending invoices
    selected_invoice_id = request.GET.get('invoice') or ''
    selected_student_id = request.GET.get('student') or ''
    pending_invoices = FeeInvoice.objects.filter(
        balance__gt=0
    ).exclude(status='paid').select_related('student', 'student__current_class').order_by('-created_at')

    if selected_invoice_id:
        pending_invoices = pending_invoices.filter(pk=selected_invoice_id)
    elif selected_student_id:
        pending_invoices = pending_invoices.filter(student_id=selected_student_id)
    
    context = {
        'pending_invoices': pending_invoices,
        'today': date.today(),
        'selected_invoice_id': str(selected_invoice_id),
    }
    
    return render(request, 'frontend/finance/payment_record.html', context)


@staff_only
def payment_list(request):
    """List all payments"""
    payments = Payment.objects.select_related(
        'student', 'invoice'
    ).order_by('-payment_date')
    
    # Filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    if search:
        payments = payments.filter(
            Q(receipt_number__icontains=search) |
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search)
        )
    
    # Summary
    total_amount = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    today = date.today()
    this_month_start = today.replace(day=1)
    summary = {
        'total_collected': total_amount,
        'payment_count': payments.count(),
        'this_month': payments.filter(payment_date__date__gte=this_month_start).aggregate(Sum('amount'))['amount__sum'] or 0,
        'today': payments.filter(payment_date__date=today).aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    
    # Pagination
    paginator = Paginator(payments, 50)
    page = request.GET.get('page', 1)
    payments_page = paginator.get_page(page)
    
    context = {
        'payments': payments_page,
        'total_amount': total_amount,
        'summary': summary,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
    }
    
    return render(request, 'frontend/finance/payment_list.html', context)


@staff_only
def payment_detail(request, pk):
    """Payment detail page"""
    payment = get_object_or_404(
        Payment.objects.select_related('student', 'invoice', 'recorded_by'),
        pk=pk
    )
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'frontend/finance/payment_detail.html', context)


@staff_only
def payment_receipt(request, pk):
    """Generate and display payment receipt PDF"""
    payment = get_object_or_404(Payment, pk=pk)
    
    # Generate PDF
    pdf_path: str = _generate_receipt_pdf(payment)
    
    # Serve PDF
    with open(pdf_path, 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{payment.receipt_number}.pdf"'
        return response


@staff_only
def accounts_list(request):
    """List of student accounts with balances"""
    students = Student.objects.filter(
        status='active'
    ).annotate(
        total_balance=Sum('fee_invoices__balance')
    ).filter(total_balance__gt=0).order_by('-total_balance')
    
    # Filters
    grade_filter = request.GET.get('grade', '')
    if grade_filter:
        students = students.filter(current_class__grade_id=grade_filter)
    
    # Summary
    total_outstanding = students.aggregate(Sum('total_balance'))['total_balance__sum'] or 0
    
    context = {
        'students': students,
        'total_outstanding': total_outstanding,
    }
    
    return render(request, 'frontend/finance/accounts_list.html', context)


@staff_only
def student_account(request, student_id):
    """Student account statement"""
    student = get_object_or_404(Student, pk=student_id)
    
    # Get all invoices and payments
    invoices = FeeInvoice.objects.filter(student=student).order_by('issue_date')
    payments = Payment.objects.filter(student=student).order_by('payment_date')
    
    # Calculate totals
    total_invoiced = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_invoiced - total_paid
    
    context = {
        'student': student,
        'invoices': invoices,
        'payments': payments,
        'total_invoiced': total_invoiced,
        'total_paid': total_paid,
        'balance': balance,
    }
    
    return render(request, 'frontend/finance/student_account.html', context)


@staff_only
def arrears_list(request):
    """List of students with arrears"""
    students = Student.objects.filter(
        status='active'
    ).annotate(total_balance=Sum('fee_invoices__balance')).filter(
        total_balance__gt=0
    ).order_by('-total_balance')
    
    # Aging analysis
    overdue_30 = students.filter(
        fee_invoices__due_date__lt=date.today() - timedelta(days=30),
        fee_invoices__balance__gt=0
    ).distinct().count()
    
    overdue_60 = students.filter(
        fee_invoices__due_date__lt=date.today() - timedelta(days=60),
        fee_invoices__balance__gt=0
    ).distinct().count()
    
    overdue_90 = students.filter(
        fee_invoices__due_date__lt=date.today() - timedelta(days=90),
        fee_invoices__balance__gt=0
    ).distinct().count()
    
    context = {
        'students': students,
        'overdue_30': overdue_30,
        'overdue_60': overdue_60,
        'overdue_90': overdue_90,
    }
    
    return render(request, 'frontend/finance/arrears_list.html', context)


@bursar_or_manager
def send_reminders(request):
    """Send payment reminder emails"""
    if request.method == 'POST':
        reminder_type = request.POST.get('type')  # 'soft', 'final', 'blacklist'
        student_ids = request.POST.getlist('students')
        send_email = request.POST.get('send_email') == 'on'
        send_sms = request.POST.get('send_sms') == 'on'

        from communication.email_utils import EmailSender
        from communication.sms_utils import SmsSender
        
        try:
            outstanding_invoices = FeeInvoice.objects.filter(balance__gt=0).select_related('student', 'student__parent', 'student__current_class')
            if student_ids:
                outstanding_invoices = outstanding_invoices.filter(student_id__in=student_ids)

            groups = _build_parent_balance_groups(outstanding_invoices)
            delivered = 0

            for group in groups:
                context = _build_reminder_context(group, reminder_type)
                email_sent = False
                sms_sent = False

                if send_email and group['email_address']:
                    EmailSender.send_email(
                        subject=f'Fee Payment Reminder - {group["recipient_name"]}',
                        to_emails=[group['email_address']],
                        template_name='payment_reminder',
                        context=context,
                    )
                    email_sent = True

                if send_sms and group['phone_number']:
                    SmsSender.send_payment_reminder(group['phone_number'], context)
                    sms_sent = True

                reminder_summary = render_to_string('sms/payment_reminder.txt', context).strip()
                for child in group['children']:
                    PaymentReminder.objects.create(
                        student_id=child['student_id'],
                        reminder_type=reminder_type,
                        outstanding_amount=child['balance'],
                        payment_deadline=child['due_date'],
                        letter_content=reminder_summary,
                        status='sent',
                        sent_via_email=email_sent,
                        email_sent_at=timezone.now() if email_sent else None,
                        sent_via_sms=sms_sent,
                        sms_sent_at=timezone.now() if sms_sent else None,
                        generated_by=request.user,
                    )

                if email_sent or sms_sent:
                    delivered += 1

            messages.success(request, f'{delivered} parent reminder message(s) sent!')
            return redirect('frontend:arrears_list')
        
        except Exception as e:
            messages.error(request, f'Error sending reminders: {str(e)}')
    
    return redirect('frontend:arrears_list')


@bursar_or_manager
def expense_list(request):
    """List of expenses"""
    expenses = Expense.objects.all().order_by('-expense_date')
    
    # Filters
    category_filter = request.GET.get('category', '')
    if category_filter:
        expenses = expenses.filter(category=category_filter)
    
    # Summary
    total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Pagination
    paginator = Paginator(expenses, 50)
    page = request.GET.get('page', 1)
    expenses_page = paginator.get_page(page)
    
    context = {
        'expenses': expenses_page,
        'total': total,
    }
    
    return render(request, 'frontend/finance/expense_list.html', context)


@bursar_or_manager
def expense_add(request):
    """Add new expense"""
    if request.method == 'POST':
        try:
            from administration.notification_utils import send_approval_notification

            expense = Expense.objects.create(
                description=request.POST.get('description'),
                category=request.POST.get('category'),
                amount=float(request.POST.get('amount')),
                expense_date=request.POST.get('expense_date'),
                recorded_by=request.user
            )

            send_approval_notification(
                notification_type='expense_request',
                title=f'New Expense Recorded: {request.POST.get("description", "Expense")[:50]}',
                message=f'{request.user.get_full_name()} recorded a new expense for approval review.',
                related_object=expense,
                recipient_user_types=['admin', 'manager']
            )
            
            messages.success(request, 'Expense recorded successfully!')
            return redirect('frontend:expense_list')
        
        except Exception as e:
            messages.error(request, f'Error recording expense: {str(e)}')
    
    return render(request, 'frontend/finance/expense_add.html')
