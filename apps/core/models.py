from django.conf import settings
from django.db import models


class Transaction(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	transaction_type = models.CharField(max_length=20)
	timestamp = models.DateTimeField(auto_now_add=True)
	description = models.TextField(blank=True)

	def __str__(self):
		return f"Transaction {self.id} - {self.user} - {self.amount}"
