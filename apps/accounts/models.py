from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Fintech specific fields
    is_lender = models.BooleanField(default=False)
    is_borrower = models.BooleanField(default=False)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.username} ({'Lender' if self.is_lender else 'Borrower'})"