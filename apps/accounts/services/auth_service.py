from django.contrib.auth import login
from django.db import transaction
from ..models import User

class AuthService:
    @staticmethod
    @transaction.atomic
    def register_user(request, form, role=User.Role.BORROWER, email=''):
        user = form.save(commit=False)
        user.email = email
        user.role = role
        user.save()
        login(request, user)
        return user
