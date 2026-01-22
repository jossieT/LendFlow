from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Transaction
from loans.models import Loan
from loan_applications.models import LoanApplication
from django.db.models import Sum
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django import forms
from django.shortcuts import redirect

@login_required
def dashboard(request):
    # 'request.user' contains the Custom User object we created
    user = request.user

    loans = Loan.objects.filter(borrower=user)
    active_loans = loans.filter(is_active=True)
    total_borrowed = loans.aggregate(total=Sum('principal'))['total'] or 0
    total_outstanding = active_loans.aggregate(total=Sum('principal'))['total'] or 0

    recent_transactions = (
        Transaction.objects.filter(user=user)
        .order_by('-timestamp')[:10]
    )

    # compute a simple total_interest placeholder (could be computed from payments)
    total_interest = Transaction.objects.filter(user=user, transaction_type='interest').aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'user': user,
        'balance': user.balance,
        'loans': loans,
        'active_loans': active_loans,
        'total_borrowed': total_borrowed,
        'total_outstanding': total_outstanding,
        'total_interest': total_interest,
        'recent_transactions': recent_transactions,
        'now': timezone.now(),
    }
    return render(request, 'core/dashboard_tailwind.html', context)


@login_required
def htmx_loans(request):
    user = request.user
    loans_qs = Loan.objects.filter(borrower=user).order_by('-created_at')
    page = request.GET.get('page', 1)
    paginator = Paginator(loans_qs, 5)
    loans_page = paginator.get_page(page)

    html = render_to_string('core/_loans_list.html', {'active_loans': loans_page})
    return HttpResponse(html)


@login_required
def htmx_transactions(request):
    user = request.user
    tx_qs = Transaction.objects.filter(user=user).order_by('-timestamp')
    page = request.GET.get('page', 1)
    paginator = Paginator(tx_qs, 10)
    tx_page = paginator.get_page(page)

    html = render_to_string('core/_transactions_list.html', {'recent_transactions': tx_page})
    return HttpResponse(html)


@login_required
def htmx_loans_chart(request):
    user = request.user
    # Simple chart data: last 6 loans amounts
    recent = Loan.objects.filter(borrower=user).order_by('-disbursement_date')[:6]
    labels = [l.disbursement_date.strftime('%b %d') for l in recent][::-1]
    data = [float(l.principal) for l in recent][::-1]

    html = render_to_string('core/_loans_chart.html', {'labels': labels, 'data': data})
    return HttpResponse(html)


class ApplyLoanForm(forms.ModelForm):
    class Meta:
        # Note: ApplyLoanForm should probably use LoanApplication now
        model = LoanApplication
        fields = ['amount', 'term', 'remarks']


from .services.loan_service import LoanService, LedgerService

@login_required
@require_http_methods(["GET", "POST"])
def htmx_apply_loan(request):
    user = request.user
    if request.method == 'POST':
        form = ApplyLoanForm(request.POST)
        if form.is_valid():
            # Legacy service call — this should be refactored to use the new flow
            # For now, just create a Draft application
            LoanApplication.objects.create(
                borrower=user,
                amount=form.cleaned_data['amount'],
                term=form.cleaned_data['term'],
                remarks=form.cleaned_data.get('remarks', ''),
                created_by=user
            )
            return HttpResponse("<div>Loan application submitted.</div>")
    else:
        form = ApplyLoanForm()

    html = render_to_string('core/_apply_loan.html', {'form': form}, request=request)
    return HttpResponse(html)


class RepayForm(forms.Form):
    amount = forms.DecimalField(max_digits=12, decimal_places=2)
    description = forms.CharField(required=False)


@login_required
@require_http_methods(["GET", "POST"])
def htmx_repay(request):
    user = request.user
    if request.method == 'POST':
        form = RepayForm(request.POST)
        if form.is_valid():
            # Use Service Layer
            LedgerService.record_deposit(
                user=user,
                amount=form.cleaned_data['amount'],
                description=form.cleaned_data.get('description', '')
            )
            return HttpResponse("<div>Repayment recorded.</div>")
    else:
        form = RepayForm()

    html = render_to_string('core/_repay.html', {'form': form}, request=request)
    return HttpResponse(html)


@login_required
def lender_dashboard(request):
    from accounts.models import User
    # Redirect borrowers to borrower dashboard
    if request.user.role != User.Role.LOAN_OFFICER:
        return redirect('dashboard')

    # Basic data population (replace with richer queries as needed)
    active_investments = Loan.objects.filter(is_active=True)
    total_invested = active_investments.aggregate(total=Sum('principal'))['total'] or 0
    expected_returns = total_invested * Decimal('0.06') if total_invested else 0
    net_profit = Transaction.objects.filter(transaction_type='interest').aggregate(total=Sum('amount'))['total'] or 0

    available_loans = LoanApplication.objects.filter(status=LoanApplication.Status.SUBMITTED)[:5]

    # Simple placeholders for diversification and calendar
    diversification = {
        'Business': 45,
        'Personal': 35,
        'Education': 20,
    }

    repayment_calendar = []

    context = {
        'total_invested': total_invested,
        'expected_returns': expected_returns,
        'net_profit': net_profit,
        'weighted_risk': 'B',
        'diversification': diversification,
        'diversification_total': '100%',
        'available_loans': available_loans,
        'repayment_calendar': repayment_calendar,
        'active_investments': active_investments,
    }
    return render(request, 'core/lender_dashboard.html', context)


@login_required
def login_router(request):
    """
    Redirect users after login based on role.
    """
    from accounts.models import User
    user = request.user
    if user.role == User.Role.LOAN_OFFICER:
        return redirect('lender_dashboard')
    if user.role == User.Role.BORROWER:
        return redirect('dashboard')
    # fallback
    if user.is_staff or user.is_superuser:
        return redirect('admin:index')
    return redirect('dashboard')


@login_required
def profile(request):
    user = request.user
    # Basic profile context — expand as needed
    recent_transactions = Transaction.objects.filter(user=user).order_by('-timestamp')[:5]
    from accounts.models import User
    loans = Loan.objects.filter(borrower=user) if user.role == User.Role.BORROWER else Loan.objects.none()
    context = {
        'user': user,
        'recent_transactions': recent_transactions,
        'loans': loans,
    }
    return render(request, 'core/profile.html', context)