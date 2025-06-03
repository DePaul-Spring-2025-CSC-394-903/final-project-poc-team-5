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
    current_age = models.IntegerField()
    retirement_age = models.IntegerField()
    projected_balance = models.DecimalField(max_digits=12, decimal_places=2)
    init_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    contribution = models.DecimalField(max_digits=5, decimal_places=2)


    total_employee_contrib = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_employer_contrib = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    def __str__(self):
        return f"401k Result: ${self.projected_balance} in {self.year_of_retirement}"

class BudgetCalculation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2)
    savings_goal = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
class SavingsCalculation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    initial_amount = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_contribution = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    duration_years = models.IntegerField()
    total_saved = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - Saved ${self.total_saved} by {self.created_at.date()}"

class MortgageCalculation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    home_price = models.DecimalField(max_digits=12, decimal_places=2)
    down_payment = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    term_years = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2)
    total_payment = models.DecimalField(max_digits=12, decimal_places=2)
    total_interest = models.DecimalField(max_digits=12, decimal_places=2)
    payoff_date = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user.username} - ${self.monthly_payment}/mo for {self.term_years} years"


class TakeHomeCalculation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    income = models.DecimalField(max_digits=12, decimal_places=2)
    filing_status = models.CharField(max_length=20)
    state = models.CharField(max_length=2)
    frequency = models.CharField(max_length=20)
    take_home_annual = models.DecimalField(max_digits=12, decimal_places=2)
    take_home_per_period = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.user.username} - {self.created_at.date()} - ${self.take_home_annual}"


