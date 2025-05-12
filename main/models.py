from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.contrib.postgres.fields import JSONField

class DebtCalculation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    months_to_freedom = models.IntegerField()
    total_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    loan_summary = models.TextField(blank=True, default="")

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%b %d, %Y %H:%M')}"