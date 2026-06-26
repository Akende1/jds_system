from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, Count, DecimalField
from django.db.models.functions import Coalesce
from django.contrib import messages
from datetime import date, timedelta, datetime
from decimal import Decimal
import json
from django.utils import timezone
from administration.models import Staff
from administration.decorators import manager_required, head_teacher_or_manager
from hr.models import (
    Payroll, PayrollStructure, PayrollComponent,
    StaffAllowance, StaffDeduction, PaySlip, PaySlipAllowance, 
    PaySlipDeduction, PayslipBatch
)
from finance.models import Expense, Payment, FeeInvoice


@manager_required
def financial_overview(request):
    """Main financial hub with Student Finance and Company Finance views"""
    today = date.today()
    current_month = today.replace(day=1)
    current_year = today.year
    
    # Income Summary (This Month)
    month_income = Payment.objects.filter(
        payment_date__year=current_month.year,
        payment_date__month=current_month.month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Expected Income (Outstanding invoices)
    expected_income = FeeInvoice.objects.filter(
        status__in=['pending', 'partially_paid']
    ).aggregate(total=Sum('balance'))['total'] or 0
    
    # Expenses Summary (This Month)
    month_expenses = Expense.objects.filter(
        expense_date__year=current_month.year,
        expense_date__month=current_month.month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Salary Summary (This Month)
    month_salaries = Payroll.objects.filter(
        month=current_month,
        status='paid'
    ).aggregate(total=Sum('net_salary'))['total'] or 0
    
    # Total expenses including salaries
    total_expenses = (month_expenses or 0) + (month_salaries or 0)
    
    # Net balance
    net_balance = month_income - total_expenses
    
    # Year-to-date summary
    year_start = date(current_year, 1, 1)
    ytd_income = Payment.objects.filter(
        payment_date__gte=year_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    ytd_expenses = Expense.objects.filter(
        expense_date__gte=year_start
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    ytd_salaries = Payroll.objects.filter(
        month__gte=year_start,
        status='paid'
    ).aggregate(total=Sum('net_salary'))['total'] or 0
    
    ytd_total_expenses = (ytd_expenses or 0) + (ytd_salaries or 0)
    ytd_net = ytd_income - ytd_total_expenses
    
    # Monthly trend data (Last 6 months)
    monthly_data = []
    for i in range(6):
        month_date = current_month - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        
        income = Payment.objects.filter(
            payment_date__year=month_start.year,
            payment_date__month=month_start.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expenses = Expense.objects.filter(
            expense_date__year=month_start.year,
            expense_date__month=month_start.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        salaries = Payroll.objects.filter(
            month=month_start,
            status='paid'
        ).aggregate(total=Sum('net_salary'))['total'] or 0
        
        monthly_data.append({
            'month': month_start.strftime('%b %Y'),
            'income': float(income),
            'expenses': float(expenses + salaries)
        })
    
    monthly_data.reverse()

    # Student finance summary: the fee ledger side of the business
    student_finance = {
        'projected_earnings': float(expected_income + ytd_income),
        'collected': float(ytd_income),
        'outstanding': float(expected_income),
        'collection_rate': float((ytd_income / (expected_income + ytd_income) * 100) if (expected_income + ytd_income) else 0),
    }

    # Company finance summary: school business P&L, where fees become income
    company_finance = {
        'income': float(ytd_income),
        'operating_expenses': float(ytd_expenses),
        'payroll': float(ytd_salaries),
        'net_balance': float(ytd_net),
    }
    
    # Expense breakdown by category
    expense_by_category = Expense.objects.filter(
        expense_date__year=current_month.year,
        expense_date__month=current_month.month
    ).values('category').annotate(total=Sum('amount')).order_by('-total')
    
    context = {
        # This Month
        'month_income': month_income,
        'month_expenses': month_expenses,
        'month_salaries': month_salaries,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
        'expected_income': expected_income,
        
        # Year to Date
        'ytd_income': ytd_income,
        'ytd_expenses': ytd_expenses,
        'ytd_salaries': ytd_salaries,
        'ytd_total_expenses': ytd_total_expenses,
        'ytd_net': ytd_net,
        
        # Charts
        'monthly_data': monthly_data,
        'monthly_data_json': json.dumps(monthly_data),
        'expense_by_category': list(expense_by_category),
        'expense_by_category_json': json.dumps(list(expense_by_category)),

        # Streamlined finance sections
        'student_finance': student_finance,
        'company_finance': company_finance,
        
        'current_month': current_month,
    }
    
    return render(request, 'frontend/financial/overview.html', context)


@manager_required
def income_list(request):
    """List all income (payments from students)"""
    payments = Payment.objects.select_related('student', 'invoice').order_by('-payment_date')
    
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
            Q(student__user__first_name__icontains=search) |
            Q(student__user__last_name__icontains=search)
        )
    
    total_income = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Expected income from outstanding invoices
    expected_income = FeeInvoice.objects.filter(
        status__in=['pending', 'partially_paid']
    ).aggregate(total=Sum('balance'))['total'] or 0
    
    context = {
        'payments': payments[:100],
        'total_income': total_income,
        'expected_income': expected_income,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
    }
    
    return render(request, 'frontend/financial/income_list.html', context)


@manager_required
def expense_list(request):
    """List and manage expenses"""
    expenses = Expense.objects.order_by('-expense_date')
    
    # Filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    category = request.GET.get('category', '')
    
    if date_from:
        expenses = expenses.filter(expense_date__gte=date_from)
    if date_to:
        expenses = expenses.filter(expense_date__lte=date_to)
    if category:
        expenses = expenses.filter(category=category)
    
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get all categories
    categories = Expense.objects.values_list('category', flat=True).distinct()
    
    context = {
        'expenses': expenses[:100],
        'total_expenses': total_expenses,
        'categories': categories,
        'date_from': date_from,
        'date_to': date_to,
        'category': category,
    }
    
    return render(request, 'frontend/financial/expense_list.html', context)


@manager_required
def expense_add(request):
    """Add new expense"""
    if request.method == 'POST':
        # Generate expense number
        last_expense = Expense.objects.order_by('-id').first()
        if last_expense and last_expense.expense_number:
            try:
                last_num = int(last_expense.expense_number.split('-')[-1])
                new_num = f"EXP-{last_num + 1:05d}"
            except:
                new_num = f"EXP-{date.today().year}{date.today().month:02d}001"
        else:
            new_num = f"EXP-{date.today().year}{date.today().month:02d}001"
        
        category = request.POST.get('category', '').lower()
        
        Expense.objects.create(
            expense_number=new_num,
            title=request.POST.get('description', 'Expense')[:200],
            category=category,
            description=request.POST.get('description', ''),
            amount=request.POST.get('amount'),
            expense_date=request.POST.get('date'),
            payment_status='paid',
            payment_method=request.POST.get('payment_method', 'cash'),
            vendor_name=request.POST.get('vendor', ''),
            invoice_reference=request.POST.get('reference', ''),
            approved_by=request.user.get_full_name()
        )
        
        messages.success(request, 'Expense recorded successfully!')
        return redirect('frontend:expense_list')
    
    today = date.today()
    
    context = {
        'today': today,
    }
    
    return render(request, 'frontend/financial/expense_add.html', context)


@manager_required
def salary_list(request):
    """List all salary payments"""
    salaries = Payroll.objects.select_related('staff', 'staff__user').order_by('-month')
    
    # Filters
    month = request.GET.get('month', '')
    status = request.GET.get('status', '')
    
    if month:
        month_date = date.fromisoformat(month + '-01')
        salaries = salaries.filter(month=month_date)
    if status:
        salaries = salaries.filter(status=status)
    
    total_salaries = salaries.aggregate(Sum('net_salary'))['net_salary__sum'] or 0
    paid_salaries = salaries.filter(status='paid').aggregate(Sum('net_salary'))['net_salary__sum'] or 0
    
    context = {
        'salaries': salaries[:100],
        'total_salaries': total_salaries,
        'paid_salaries': paid_salaries,
        'month': month,
        'status': status,
    }
    
    return render(request, 'frontend/financial/salary_list.html', context)


@manager_required
def salary_detail(request, pk):
    """View salary payment details"""
    salary = get_object_or_404(Payroll.objects.select_related('staff', 'staff__user'), pk=pk)
    
    # Get all items
    earnings = salary.items.filter(component__component_type='earning').select_related('component')
    deductions = salary.items.filter(component__component_type='deduction').select_related('component')
    
    context = {
        'salary': salary,
        'earnings': earnings,
        'deductions': deductions,
    }
    
    return render(request, 'frontend/financial/salary_detail.html', context)


@manager_required
def financial_reports(request):
    """Generate financial reports"""
    # Get date range
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if not date_from:
        date_from = date.today().replace(day=1)
    else:
        date_from = date.fromisoformat(date_from)
    
    if not date_to:
        date_to = date.today()
    else:
        date_to = date.fromisoformat(date_to)
    
    # Income
    income = Payment.objects.filter(
        payment_date__gte=date_from,
        payment_date__lte=date_to
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    income_by_method = Payment.objects.filter(
        payment_date__gte=date_from,
        payment_date__lte=date_to
    ).values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Expenses
    expenses = Expense.objects.filter(
        expense_date__gte=date_from,
        expense_date__lte=date_to
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    expense_by_category = Expense.objects.filter(
        expense_date__gte=date_from,
        expense_date__lte=date_to
    ).values('category').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Salaries
    salaries = Payroll.objects.filter(
        month__gte=date_from,
        month__lte=date_to,
        status='paid'
    ).aggregate(total=Sum('net_salary'))['total'] or 0
    
    # Totals
    total_expenses = (expenses or 0) + (salaries or 0)
    net_profit = income - total_expenses
    
    # Add percentages for expense categories
    expense_by_category_list = list(expense_by_category)
    for exp_cat in expense_by_category_list:
        exp_cat['percentage'] = (exp_cat['total'] / expenses * 100) if expenses > 0 else 0
    
    total_expense_count = sum(item['count'] for item in expense_by_category_list)
    
    # Calculate total payments count
    income_by_method_list = list(income_by_method)
    total_payments = sum(item['count'] for item in income_by_method_list)
    
    context = {
        'date_from': date_from,
        'date_to': date_to,
        'total_income': income,
        'total_expenses': expenses,
        'total_salaries': salaries,
        'net_profit': net_profit,
        'income_by_method': income_by_method_list,
        'expense_by_category': expense_by_category_list,
        'total_payments': total_payments,
        'total_expense_count': total_expense_count,
    }
    
    return render(request, 'frontend/financial/reports.html', context)


@manager_required
def payroll_generate(request):
    """Generate payroll for a month"""
    if request.method == 'POST':
        from administration.notification_utils import send_approval_notification

        month = request.POST.get('month')
        staff_ids = request.POST.getlist('staff')
        
        month_date = date.fromisoformat(month + '-01')
        
        for staff_id in staff_ids:
            staff = Staff.objects.get(id=staff_id)
            
            # Check if payroll already exists
            if Payroll.objects.filter(staff=staff, month=month_date).exists():
                continue
            
            # Create payroll
            payroll = Payroll.objects.create(
                staff=staff,
                month=month_date,
                basic_salary=float(request.POST.get(f'basic_{staff_id}', 0)),
                status='pending'
            )
            
            # Add earnings
            earnings = PayrollStructure.objects.filter(component_type='earning', is_active=True)
            for earning in earnings:
                amount = float(request.POST.get(f'earning_{earning.id}_{staff_id}', 0))
                if amount > 0:
                    PayrollItem.objects.create(
                        payroll=payroll,
                        component=earning,
                        amount=amount
                    )
            
            # Add deductions
            deductions = PayrollStructure.objects.filter(component_type='deduction', is_active=True)
            for deduction in deductions:
                amount = float(request.POST.get(f'deduction_{deduction.id}_{staff_id}', 0))
                if amount > 0:
                    PayrollItem.objects.create(
                        payroll=payroll,
                        component=deduction,
                        amount=amount
                    )
            
            # Calculate totals
            total_earnings = payroll.items.filter(component__component_type='earning').aggregate(Sum('amount'))['amount__sum'] or 0
            total_deductions = payroll.items.filter(component__component_type='deduction').aggregate(Sum('amount'))['amount__sum'] or 0
            
            payroll.total_earnings = payroll.basic_salary + total_earnings
            payroll.total_deductions = total_deductions
            payroll.net_salary = payroll.total_earnings - payroll.total_deductions
            payroll.save()

            send_approval_notification(
                notification_type='expense_request',
                title=f'Payroll Pending Approval: {staff.user.get_full_name()}',
                message=f'Payroll generated for {staff.user.get_full_name()} for {month_date:%B %Y}.',
                related_object=payroll,
                recipient_user_types=['admin', 'manager']
            )
        
        messages.success(request, f'Payroll generated for {len(staff_ids)} staff members!')
        return redirect('frontend:payroll_dashboard')
    
    # GET - Show form
    staff_list = Staff.objects.filter(is_active=True).select_related('user')
    salary_components = PayrollStructure.objects.filter(is_active=True)
    
    context = {
        'staff_list': staff_list,
        'salary_components': salary_components,
    }
    
    return render(request, 'frontend/payroll/generate.html', context)


@manager_required
def payroll_list(request):
    """List all payroll records"""
    payrolls = Payroll.objects.select_related('staff', 'staff__user').order_by('-month', 'staff__staff_id')
    
    # Filters
    month = request.GET.get('month', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    if month:
        month_date = date.fromisoformat(month + '-01')
        payrolls = payrolls.filter(month=month_date)
    
    if status:
        payrolls = payrolls.filter(status=status)
    
    if search:
        payrolls = payrolls.filter(
            Q(staff__staff_id__icontains=search) |
            Q(staff__user__first_name__icontains=search) |
            Q(staff__user__last_name__icontains=search)
        )
    
    context = {
        'payrolls': payrolls,
        'month': month,
        'status': status,
        'search': search,
    }
    
    return render(request, 'frontend/payroll/list.html', context)


@manager_required
def payroll_detail(request, pk):
    """View payroll details"""
    payroll = get_object_or_404(Payroll.objects.select_related('staff', 'staff__user'), pk=pk)
    
    # Get all items
    earnings = payroll.items.filter(component__component_type='earning').select_related('component')
    deductions = payroll.items.filter(component__component_type='deduction').select_related('component')
    
    context = {
        'payroll': payroll,
        'earnings': earnings,
        'deductions': deductions,
    }
    
    return render(request, 'frontend/payroll/detail.html', context)


@manager_required
def payroll_mark_paid(request, pk):
    """Mark payroll as paid"""
    payroll = get_object_or_404(Payroll, pk=pk)
    
    if request.method == 'POST':
        payroll.status = 'paid'
        payroll.paid_date = date.today()
        payroll.save()
        
        messages.success(request, f'Payroll for {payroll.staff.user.get_full_name()} marked as paid!')
        return redirect('frontend:payroll_detail', pk=pk)
    
    return redirect('frontend:payroll_detail', pk=pk)


@manager_required
def salary_components(request):
    """Manage salary components"""
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        component_type = request.POST.get('component_type')
        is_percentage = request.POST.get('is_percentage') == 'on'
        default_value = request.POST.get('default_value', 0)
        
        PayrollStructure.objects.create(
            name=name,
            code=code,
            component_type=component_type,
            is_percentage=is_percentage,
            default_value=default_value
        )
        
        messages.success(request, f'Salary component "{name}" created successfully!')
        return redirect('frontend:salary_components')
    
    components = PayrollStructure.objects.all().order_by('component_type', 'name')
    
    context = {
        'components': components,
    }
    
    return render(request, 'frontend/payroll/components.html', context)


# ============================================
# ALLOWANCES MANAGEMENT
# ============================================

@manager_required
def allowance_list(request):
    """List all active allowances"""
    allowances = StaffAllowance.objects.select_related('staff', 'staff__user').filter(
        status='active'
    ).order_by('-start_date')
    
    staff_filter = request.GET.get('staff')
    if staff_filter:
        allowances = allowances.filter(staff__id=staff_filter)
    
    allowance_type_filter = request.GET.get('type')
    if allowance_type_filter:
        allowances = allowances.filter(allowance_type=allowance_type_filter)
    
    staff_members = Staff.objects.filter(user__is_active=True).select_related('user').order_by('user__first_name')
    
    context = {
        'allowances': allowances,
        'staff_members': staff_members,
        'allowance_types': StaffAllowance.ALLOWANCE_TYPE_CHOICES,
        'selected_staff': staff_filter,
        'selected_type': allowance_type_filter,
    }
    
    return render(request, 'frontend/payroll/allowance_list.html', context)


@manager_required
def allowance_create(request, staff_id):
    """Create a new allowance for a staff member"""
    staff = get_object_or_404(Staff, pk=staff_id)
    
    if request.method == 'POST':
        allowance_type = request.POST.get('allowance_type')
        amount = request.POST.get('amount')
        frequency = request.POST.get('frequency', 'monthly')
        start_date = request.POST.get('start_date')
        reason = request.POST.get('reason', '')
        is_taxable = request.POST.get('is_taxable') == 'on'
        
        try:
            allowance = StaffAllowance.objects.create(
                staff=staff,
                allowance_type=allowance_type,
                amount=Decimal(amount),
                frequency=frequency,
                start_date=start_date,
                reason=reason,
                is_taxable=is_taxable,
                approved_by=request.user,
                approval_date=timezone.now().date(),
            )
            messages.success(request, f'Allowance created successfully for {staff.user.get_full_name()}')
            return redirect('frontend:payroll_allowance_detail', pk=allowance.pk)
        except Exception as e:
            messages.error(request, f'Error creating allowance: {str(e)}')
    
    context = {
        'staff': staff,
        'allowance_types': StaffAllowance.ALLOWANCE_TYPE_CHOICES,
        'frequencies': StaffAllowance.FREQUENCY_CHOICES,
    }
    
    return render(request, 'frontend/payroll/allowance_form.html', context)


@manager_required
def allowance_detail(request, pk):
    """View allowance details"""
    allowance = get_object_or_404(StaffAllowance.objects.select_related('staff', 'staff__user', 'approved_by'), pk=pk)
    
    impact_data = None
    if allowance.is_active():
        payslips = PaySlip.objects.filter(
            staff=allowance.staff,
            payslip_period_start__gte=allowance.start_date
        ).order_by('-payslip_period_end')[:6]
        
        impact_data = {
            'recent_payslips': payslips,
            'total_paid_this_year': payslips.aggregate(
                total=Sum('total_allowances')
            )['total'] or Decimal('0.00'),
        }
    
    context = {
        'allowance': allowance,
        'impact_data': impact_data,
    }
    
    return render(request, 'frontend/payroll/allowance_detail.html', context)


@manager_required
def allowance_edit(request, pk):
    """Edit an allowance"""
    allowance = get_object_or_404(StaffAllowance, pk=pk)
    
    if allowance.status != 'active':
        messages.error(request, 'Only active allowances can be edited')
        return redirect('frontend:payroll_allowance_detail', pk=pk)
    
    if request.method == 'POST':
        allowance.amount = Decimal(request.POST.get('amount'))
        allowance.frequency = request.POST.get('frequency')
        allowance.reason = request.POST.get('reason', '')
        allowance.is_taxable = request.POST.get('is_taxable') == 'on'
        allowance.save()
        
        messages.success(request, 'Allowance updated successfully')
        return redirect('frontend:payroll_allowance_detail', pk=pk)
    
    context = {
        'allowance': allowance,
        'frequencies': StaffAllowance.FREQUENCY_CHOICES,
    }
    
    return render(request, 'frontend/payroll/allowance_edit.html', context)


@manager_required
def allowance_end(request, pk):
    """End an active allowance"""
    allowance = get_object_or_404(StaffAllowance, pk=pk)
    
    if request.method == 'POST':
        allowance.status = 'ended'
        allowance.end_date = timezone.now().date()
        allowance.save()
        
        messages.success(request, f'Allowance ended on {allowance.end_date}')
        return redirect('frontend:payroll_allowance_detail', pk=pk)
    
    return render(request, 'frontend/payroll/allowance_confirm_end.html', {'allowance': allowance})


# ============================================
# DEDUCTIONS MANAGEMENT
# ============================================

@manager_required
def deduction_list(request):
    """List all active deductions"""
    deductions = StaffDeduction.objects.select_related('staff', 'staff__user').filter(
        status='active'
    ).order_by('-start_date')
    
    staff_filter = request.GET.get('staff')
    if staff_filter:
        deductions = deductions.filter(staff__id=staff_filter)
    
    deduction_type_filter = request.GET.get('type')
    if deduction_type_filter:
        deductions = deductions.filter(deduction_type=deduction_type_filter)
    
    staff_members = Staff.objects.filter(user__is_active=True).select_related('user').order_by('user__first_name')
    
    context = {
        'deductions': deductions,
        'staff_members': staff_members,
        'deduction_types': StaffDeduction.DEDUCTION_TYPE_CHOICES,
        'selected_staff': staff_filter,
        'selected_type': deduction_type_filter,
    }
    
    return render(request, 'frontend/payroll/deduction_list.html', context)


@manager_required
def deduction_create(request, staff_id):
    """Create a new deduction for a staff member"""
    staff = get_object_or_404(Staff, pk=staff_id)
    
    if request.method == 'POST':
        deduction_type = request.POST.get('deduction_type')
        amount = request.POST.get('amount')
        frequency = request.POST.get('frequency', 'monthly')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason', '')
        is_fixed = request.POST.get('is_fixed') == 'on'
        percentage = request.POST.get('percentage_of_salary')
        
        try:
            deduction = StaffDeduction.objects.create(
                staff=staff,
                deduction_type=deduction_type,
                amount=Decimal(amount) if is_fixed else Decimal('0'),
                frequency=frequency,
                start_date=start_date,
                end_date=end_date if end_date else None,
                reason=reason,
                is_fixed=is_fixed,
                percentage_of_salary=Decimal(percentage) if percentage else None,
                approved_by=request.user,
                approval_date=timezone.now().date(),
            )
            messages.success(request, f'Deduction created successfully for {staff.user.get_full_name()}')
            return redirect('frontend:payroll_deduction_detail', pk=deduction.pk)
        except Exception as e:
            messages.error(request, f'Error creating deduction: {str(e)}')
    
    context = {
        'staff': staff,
        'deduction_types': StaffDeduction.DEDUCTION_TYPE_CHOICES,
        'frequencies': StaffDeduction.FREQUENCY_CHOICES,
    }
    
    return render(request, 'frontend/payroll/deduction_form.html', context)


@manager_required
def deduction_detail(request, pk):
    """View deduction details"""
    deduction = get_object_or_404(StaffDeduction.objects.select_related('staff', 'staff__user', 'approved_by'), pk=pk)
    
    impact_data = None
    if deduction.is_active():
        payslips = PaySlip.objects.filter(
            staff=deduction.staff,
            payslip_period_start__gte=deduction.start_date
        ).order_by('-payslip_period_end')[:6]
        
        impact_data = {
            'recent_payslips': payslips,
            'total_deducted_this_year': payslips.aggregate(
                total=Sum('total_deductions')
            )['total'] or Decimal('0.00'),
        }
    
    context = {
        'deduction': deduction,
        'impact_data': impact_data,
    }
    
    return render(request, 'frontend/payroll/deduction_detail.html', context)


@manager_required
def deduction_edit(request, pk):
    """Edit a deduction"""
    deduction = get_object_or_404(StaffDeduction, pk=pk)
    
    if deduction.status != 'active':
        messages.error(request, 'Only active deductions can be edited')
        return redirect('frontend:payroll_deduction_detail', pk=pk)
    
    if request.method == 'POST':
        deduction.amount = Decimal(request.POST.get('amount')) if request.POST.get('is_fixed') == 'on' else Decimal('0')
        deduction.frequency = request.POST.get('frequency')
        deduction.is_fixed = request.POST.get('is_fixed') == 'on'
        deduction.percentage_of_salary = Decimal(request.POST.get('percentage_of_salary')) if request.POST.get('percentage_of_salary') else None
        deduction.reason = request.POST.get('reason', '')
        deduction.save()
        
        messages.success(request, 'Deduction updated successfully')
        return redirect('frontend:payroll_deduction_detail', pk=pk)
    
    context = {
        'deduction': deduction,
        'frequencies': StaffDeduction.FREQUENCY_CHOICES,
    }
    
    return render(request, 'frontend/payroll/deduction_edit.html', context)


@manager_required
def deduction_end(request, pk):
    """End an active deduction"""
    deduction = get_object_or_404(StaffDeduction, pk=pk)
    
    if request.method == 'POST':
        deduction.status = 'ended'
        deduction.end_date = timezone.now().date()
        deduction.save()
        
        messages.success(request, f'Deduction ended on {deduction.end_date}')
        return redirect('frontend:payroll_deduction_detail', pk=pk)
    
    return render(request, 'frontend/payroll/deduction_confirm_end.html', {'deduction': deduction})


# ============================================
# PAYSLIPS MANAGEMENT
# ============================================

@head_teacher_or_manager
def payslip_list(request):
    """List payslips"""
    payslips = PaySlip.objects.select_related('staff', 'staff__user').order_by('-payslip_period_end')
    
    staff_filter = request.GET.get('staff')
    if staff_filter:
        payslips = payslips.filter(staff__id=staff_filter)
    
    status_filter = request.GET.get('status')
    if status_filter:
        payslips = payslips.filter(status=status_filter)
    
    period_from = request.GET.get('from')
    if period_from:
        try:
            from_date = datetime.strptime(period_from, '%Y-%m-%d').date()
            payslips = payslips.filter(payslip_period_start__gte=from_date)
        except:
            pass
    
    staff_members = Staff.objects.filter(user__is_active=True).select_related('user').order_by('user__first_name')
    
    context = {
        'payslips': payslips[:100],
        'staff_members': staff_members,
        'statuses': PaySlip.STATUS_CHOICES,
        'selected_staff': staff_filter,
        'selected_status': status_filter,
        'selected_from': period_from,
    }
    
    return render(request, 'frontend/payroll/payslip_list.html', context)


@head_teacher_or_manager
def payslip_detail(request, pk):
    """View detailed payslip with breakdown"""
    payslip = get_object_or_404(
        PaySlip.objects.select_related('staff', 'staff__user', 'generated_by', 'approved_by'),
        pk=pk
    )
    
    allowance_items = payslip.allowance_items.select_related('allowance').order_by('description')
    deduction_items = payslip.deduction_items.select_related('deduction').order_by('description')
    
    context = {
        'payslip': payslip,
        'allowance_items': allowance_items,
        'deduction_items': deduction_items,
        'can_approve': request.user.user_type in ['admin', 'manager'] and payslip.status == 'draft',
        'can_edit': request.user.user_type in ['admin', 'manager'] and payslip.status == 'draft',
    }
    
    return render(request, 'frontend/payroll/payslip_detail.html', context)


@manager_required
def payslip_approve(request, pk):
    """Approve a draft payslip"""
    payslip = get_object_or_404(PaySlip, pk=pk)
    
    if payslip.status != 'draft':
        messages.error(request, 'Only draft payslips can be approved')
        return redirect('frontend:payroll_payslip_detail', pk=pk)
    
    if request.method == 'POST':
        payslip.status = 'approved'
        payslip.approved_by = request.user
        payslip.approval_date = timezone.now().date()
        payslip.save()
        
        messages.success(request, 'Payslip approved successfully')
        return redirect('frontend:payroll_payslip_detail', pk=pk)
    
    return render(request, 'frontend/payroll/payslip_confirm_approve.html', {'payslip': payslip})


@manager_required
def payslip_issue(request, pk):
    """Issue an approved payslip to employee"""
    payslip = get_object_or_404(PaySlip, pk=pk)
    
    if payslip.status != 'approved':
        messages.error(request, 'Only approved payslips can be issued')
        return redirect('frontend:payroll_payslip_detail', pk=pk)
    
    if request.method == 'POST':
        payslip.status = 'issued'
        payslip.save()
        
        messages.success(request, 'Payslip issued to employee')
        return redirect('frontend:payroll_payslip_detail', pk=pk)
    
    return render(request, 'frontend/payroll/payslip_confirm_issue.html', {'payslip': payslip})


@head_teacher_or_manager
def staff_payslip_history(request, staff_id):
    """View payslip history for a specific staff member"""
    staff = get_object_or_404(Staff.objects.select_related('user'), pk=staff_id)
    
    payslips = PaySlip.objects.filter(staff=staff).order_by('-payslip_period_end')
    
    stats = {
        'total_payslips': payslips.count(),
        'avg_gross': payslips.aggregate(Coalesce(Sum('gross_salary'), 0, output_field=DecimalField()))['coalesce__sum__gross_salary'] / max(payslips.count(), 1) if payslips.exists() else Decimal('0'),
        'avg_net': payslips.aggregate(Coalesce(Sum('net_salary'), 0, output_field=DecimalField()))['coalesce__sum__net_salary'] / max(payslips.count(), 1) if payslips.exists() else Decimal('0'),
    }
    
    context = {
        'staff': staff,
        'payslips': payslips[:12],
        'stats': stats,
    }
    
    return render(request, 'frontend/payroll/staff_payslip_history.html', context)


@manager_required
def payslip_batch_list(request):
    """List payslip batches"""
    batches = PayslipBatch.objects.select_related('created_by', 'approved_by').order_by('-batch_period_start')
    
    status_filter = request.GET.get('status')
    if status_filter:
        batches = batches.filter(status=status_filter)
    
    context = {
        'batches': batches,
        'statuses': PayslipBatch.BATCH_STATUS_CHOICES,
        'selected_status': status_filter,
    }
    
    return render(request, 'frontend/payroll/payslip_batch_list.html', context)


@manager_required
def payslip_batch_detail(request, pk):
    """View payslip batch details"""
    batch = get_object_or_404(
        PayslipBatch.objects.select_related('created_by', 'approved_by'),
        pk=pk
    )
    
    payslips = PaySlip.objects.filter(
        payslip_period_start=batch.batch_period_start,
        payslip_period_end=batch.batch_period_end
    ).select_related('staff', 'staff__user').order_by('staff__user__first_name')
    
    context = {
        'batch': batch,
        'payslips': payslips,
        'can_approve': request.user.user_type in ['admin', 'manager'] and batch.status == 'pending',
    }
    
    return render(request, 'frontend/payroll/payslip_batch_detail.html', context)


@manager_required
def payslip_batch_approve(request, pk):
    """Approve a batch of payslips"""
    batch = get_object_or_404(PayslipBatch, pk=pk)
    
    if batch.status != 'pending':
        messages.error(request, 'Only pending batches can be approved')
        return redirect('frontend:payroll_payslip_batch_detail', pk=pk)
    
    if request.method == 'POST':
        batch.status = 'processing'
        batch.approved_by = request.user
        batch.approval_date = timezone.now()
        batch.save()
        
        PaySlip.objects.filter(
            payslip_period_start=batch.batch_period_start,
            payslip_period_end=batch.batch_period_end
        ).update(status='approved', approved_by=request.user, approval_date=timezone.now().date())
        
        messages.success(request, 'Batch approved. All payslips updated.')
        return redirect('frontend:payroll_payslip_batch_detail', pk=pk)
    
    return render(request, 'frontend/payroll/payslip_batch_confirm_approve.html', {'batch': batch})
