from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models import JSONField

class DebtCalculation(models.Model):
    STRATEGY_CHOICES = [
        ('smallest_balance', 'Smallest Balance'),
        ('highest_interest', 'Highest Interest'),
        ('fewest_payments', 'Fewest Payments'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    strategy = models.CharField(max_length=30, choices=STRATEGY_CHOICES, default='smallest_balance')
    extra_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    months_to_freedom = models.IntegerField()
    total_balance = models.DecimalField(max_digits=10, decimal_places=2)
    total_payment = models.DecimalField(max_digits=10, decimal_places=2)
    total_interest = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    loan_summary = models.TextField(blank=True)
    loan_data = JSONField()

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%b %d, %Y %H:%M')} ({self.strategy})"
    

class RetirementCalculation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    year_of_retirement = models.IntegerField()
    init_deposit = models.DecimalField(max_digits=12, decimal_places=2)
    salary = models.DecimalField(max_digits=12, decimal_places=2)
    salary_growth = models.DecimalField(max_digits=5, decimal_places=2)
    contribution = models.DecimalField(max_digits=5, decimal_places=2)
    match = models.DecimalField(max_digits=5, decimal_places=2)
    yield_rate = models.DecimalField(max_digits=5, decimal_places=2)
    projected_balance = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"401k Result: ${self.projected_balance} in {self.year_of_retirement}"
