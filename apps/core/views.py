from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Loan, Transaction
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
    active_loans = loans.exclude(status__in=['paid', 'cancelled'])
    total_borrowed = loans.aggregate(total=Sum('amount'))['total'] or 0
    total_outstanding = active_loans.aggregate(total=Sum('amount'))['total'] or 0

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
    recent = Loan.objects.filter(borrower=user).order_by('-created_at')[:6]
    labels = [l.created_at.strftime('%b %d') for l in recent][::-1]
    data = [float(l.amount) for l in recent][::-1]

    html = render_to_string('core/_loans_chart.html', {'labels': labels, 'data': data})
    return HttpResponse(html)


class ApplyLoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['amount', 'interest_rate', 'description']


from .services.loan_service import LoanService, LedgerService

@login_required
@require_http_methods(["GET", "POST"])
def htmx_apply_loan(request):
    user = request.user
    if request.method == 'POST':
        form = ApplyLoanForm(request.POST)
        if form.is_valid():
            # Use Service Layer
            LoanService.apply_for_loan(
                user=user,
                amount=form.cleaned_data['amount'],
                interest_rate=form.cleaned_data['interest_rate'],
                description=form.cleaned_data.get('description', '')
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
            LedgerService.record_repayment(
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
    active_investments = Loan.objects.filter(borrower__isnull=False, status='active')
    total_invested = active_investments.aggregate(total=Sum('amount'))['total'] or 0
    expected_returns = active_investments.aggregate(total=Sum('amount'))['total'] and (total_invested * 0.06) or 0
    net_profit = Transaction.objects.filter(user=request.user, transaction_type='interest').aggregate(total=Sum('amount'))['total'] or 0

    available_loans = Loan.objects.filter(status='pending').exclude(borrower=request.user)[:5]

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