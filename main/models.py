from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

class DebtCalculation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    additional_payment = models.DecimalField(max_digits=10, decimal_places=2)
    months_to_freedom = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Calculation for {self.user.email} on {self.created_at.strftime('%Y-%m-%d')}"