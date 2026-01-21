from django.contrib.auth import login
from django.db import transaction

class AuthService:
    @staticmethod
    @transaction.atomic
    def register_user(request, form, role='borrower', email=''):
        user = form.save(commit=False)
        user.email = email
        user.is_lender = (role == 'lender')
        user.is_borrower = (role != 'lender')
        user.save()
        login(request, user)
        return user
