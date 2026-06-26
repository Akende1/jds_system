from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from .models import FeeInvoice, Payment, Expense, FeeStructure
from administration.models import Student
from datetime import datetime

@login_required
def invoice_list(request):
    """List all fee invoices"""
    invoices = FeeInvoice.objects.select_related(
        'student', 'student__user', 'academic_year', 'term'
    ).order_by('-issue_date')
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'paid':
        invoices = invoices.filter(balance=0)
    elif status == 'unpaid':
        invoices = invoices.filter(balance__gt=0)
    
    # Search by student
    search = request.GET.get('search')
    if search:
        invoices = invoices.filter(
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search) |
            Q(student__admission_number__icontains=search) |
            Q(invoice_number__icontains=search)
        )
    
    context = {
        'invoices': invoices[:100],
    }
    
    return render(request, 'finance/invoice_list.html', context)

@login_required
def invoice_detail(request, pk):
    """Invoice detail view"""
    invoice = get_object_or_404(
        FeeInvoice.objects.select_related(
            'student', 'student__user', 'academic_year', 'term'
        ).prefetch_related('items'),
        pk=pk
    )
    
    # Get payments for this invoice
    payments = Payment.objects.filter(invoice=invoice).order_by('-payment_date')
    
    context = {
        'invoice': invoice,
        'payments': payments,
    }
    
    return render(request, 'finance/invoice_detail.html', context)

@login_required
def payment_list(request):
    """List all payments"""
    payments = Payment.objects.select_related(
        'invoice', 'student', 'student__user'
    ).order_by('-payment_date')
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        payments = payments.filter(payment_date__gte=start_date)
    if end_date:
        payments = payments.filter(payment_date__lte=end_date)
    
    # Calculate total
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'payments': payments[:100],
        'total_amount': total_amount,
    }
    
    return render(request, 'finance/payment_list.html', context)

@login_required
def expense_list(request):
    """List all expenses"""
    expenses = Expense.objects.all().order_by('-expense_date')
    
    # Filter by category
    category = request.GET.get('category')
    if category:
        expenses = expenses.filter(category=category)
    
    # Calculate total
    total_amount = expenses.aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'expenses': expenses[:100],
        'total_amount': total_amount,
    }
    
    return render(request, 'finance/expense_list.html', context)
