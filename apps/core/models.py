from django.conf import settings
from django.db import models


class Loan(models.Model):
	borrower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
	status = models.CharField(max_length=20, default='pending')
	description = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Loan {self.id} - {self.borrower} - {self.amount}"


class Transaction(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	transaction_type = models.CharField(max_length=20)
	timestamp = models.DateTimeField(auto_now_add=True)
	description = models.TextField(blank=True)

	def __str__(self):
		return f"Transaction {self.id} - {self.user} - {self.amount}"
