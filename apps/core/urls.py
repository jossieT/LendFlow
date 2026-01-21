from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('htmx/loans/', views.htmx_loans, name='htmx_loans'),
    path('htmx/transactions/', views.htmx_transactions, name='htmx_transactions'),
    path('htmx/loans-chart/', views.htmx_loans_chart, name='htmx_loans_chart'),
    path('htmx/apply-loan/', views.htmx_apply_loan, name='htmx_apply_loan'),
    path('htmx/repay/', views.htmx_repay, name='htmx_repay'),
    path('lender/', views.lender_dashboard, name='lender_dashboard'),
    path('me/', views.profile, name='profile'),
]