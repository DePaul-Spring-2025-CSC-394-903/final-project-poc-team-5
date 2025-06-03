# main/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.forms import formset_factory
from decimal import Decimal
from datetime import date
from django.contrib.auth import authenticate

User = get_user_model()


# ──────────────────────────────────────────────────────────────────────────────
# 1) EMAIL‐BASED LOGIN FORM
# ──────────────────────────────────────────────────────────────────────────────
class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if not email or not password:
            raise forms.ValidationError("Email and password are required.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("Invalid email or password.")

        # Django’s authenticate expects a username, so we pass the user’s username:
        self.user = authenticate(username=user.username, password=password)
        if self.user is None:
            raise forms.ValidationError("Invalid email or password.")
        return cleaned_data

    def get_user(self):
        return self.user


# ──────────────────────────────────────────────────────────────────────────────
# 2) CUSTOM REGISTRATION FORM (USERCREATION)
# ──────────────────────────────────────────────────────────────────────────────
class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ("email", "password1", "password2")  # no separate username field

    def save(self, commit=True):
        user = super().save(commit=False)
        # Use the email as username
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


# ──────────────────────────────────────────────────────────────────────────────
# 3) LOAN FORM (used for Snowball/Debt Payoff)
# ──────────────────────────────────────────────────────────────────────────────
class LoanForm(forms.Form):
    name            = forms.CharField(label="Loan Name", max_length=100)
    balance         = forms.DecimalField(label="Balance ($)", min_value=0, decimal_places=2)
    interest_rate   = forms.DecimalField(label="Annual Interest Rate (%)", min_value=0, max_value=100, decimal_places=2)
    monthly_payment = forms.DecimalField(  #  ← unified name
        label="Minimum Monthly Payment ($)",        # wording good for *both* pages
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 150"})
    )

LoanFormSet = formset_factory(LoanForm, extra=1, can_delete=True)



# ──────────────────────────────────────────────────────────────────────────────
# 4) MAIN PAYMENT FORM (used in standalone Snowball view if needed)
# ──────────────────────────────────────────────────────────────────────────────
STRATEGY_CHOICES = [
    ("snowball", "Debt with smallest balance"),
    ("avalanche", "Debt with highest interest rate"),
    ("fewest_payments", "Debt with fewest payments left"),
]

class MainPaymentForm(forms.Form):
    additional_payment = forms.DecimalField(
        label="Additional Payment ($)",
        min_value=0,
        initial=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"})
    )
    strategy = forms.ChoiceField(
        label="Start Payoff With",
        choices=STRATEGY_CHOICES,
        widget=forms.Select()
    )


# ──────────────────────────────────────────────────────────────────────────────
# 5) MORTGAGE FORM
# ──────────────────────────────────────────────────────────────────────────────
class MortgageForm(forms.Form):
    home_price = forms.DecimalField(
        label="Home Price ($)",
        min_value=0,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 300000"})
    )
    down_payment = forms.DecimalField(
        label="Down Payment ($)",
        min_value=0,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "Leave blank if using %"})
    )
    down_payment_percent = forms.DecimalField(
        label="Down Payment (%)",
        min_value=0,
        max_value=100,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 10"})
    )
    interest_rate = forms.DecimalField(
        label="Interest Rate (%)",
        min_value=0,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 5"})
    )
    loan_term = forms.IntegerField(
        label="Loan Term (Years)",
        min_value=1,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 30"})
    )
    start_date = forms.CharField(
        label="Start Date (MM/YYYY)",
        required=True,
        widget=forms.TextInput(attrs={"type": "month"})
    )


# ──────────────────────────────────────────────────────────────────────────────
# 6) MERGE‐ALL CALCULATORS FORM
#    (collects only the essential inputs so the view can “auto‐fill” everything else)
# ──────────────────────────────────────────────────────────────────────────────
class MergeForm(forms.Form):
    # — TAKE‐HOME PAY FIELDS (we’ll assume 1 allowance, no local tax, etc.) —
    annual_salary = forms.DecimalField(
        label="Annual Salary ($)",
        min_value=0,
        decimal_places=2,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 75000"})
    )
    filing_status = forms.ChoiceField(
        label="Filing Status",
        choices=[
            ("single", "Single"),
            ("married", "Married Filing Jointly"),
            ("head_of_household", "Head of Household"),
        ],
        initial="single",
        required=True,
    )
    state = forms.ChoiceField(
        label="State",
        choices=[
            ("IL", "Illinois"),
            ("CA", "California"),
            ("NY", "New York"),
            # …add more states as needed…
        ],
        initial="IL",
        required=True,
    )
    pay_frequency = forms.ChoiceField(
        label="Pay Frequency",
        choices=[
            ("annual", "Annual"),
            ("monthly", "Monthly"),
            ("bi_weekly", "Bi-Weekly"),
        ],
        initial="monthly",
        required=True,
    )

    # — 401(k) FIELDS (we assume 6% annual yield, 0% salary growth) —
    current_age = forms.IntegerField(
        label="Current Age", min_value=18, initial=30, required=True
    )
    retirement_age = forms.IntegerField(
        label="Retirement Age", min_value=18, initial=65, required=True
    )
    init_401k_deposit = forms.DecimalField(
        label="401(k) Starting Balance ($)",
        min_value=0,
        decimal_places=2,
        initial=0,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 2000"})
    )
    contribution_pct = forms.DecimalField(
        label="401(k) Contribution (% of Salary)",
        min_value=0,
        max_value=100,
        decimal_places=2,
        initial=10,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 5"})
    )

    # — SAVINGS FIELDS (monthly compounding) —
    savings_initial = forms.DecimalField(
        label="Savings: Starting Balance ($)",
        min_value=0,
        decimal_places=2,
        initial=0,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 500"})
    )
    savings_years = forms.IntegerField(
        label="Savings: Years to Grow",
        min_value=1,
        initial=5,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 10"})
    )
    savings_interest = forms.DecimalField(
        label="Savings: Annual Interest (%)",
        min_value=0,
        max_value=100,
        decimal_places=2,
        initial=2,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 3"})
    )
    savings_contribution = forms.DecimalField(
        label="Savings: Monthly Contribution ($)",
        min_value=0,
        decimal_places=2,
        initial=0,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 200"})
    )
    savings_goal = forms.DecimalField(
        label="Savings Goal ($, optional)",
        min_value=0,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 20000"})
    )

    # — MORTGAGE FIELDS (we’ll assume start date = today in the view) —
    home_price = forms.DecimalField(
        label="Home Price ($)",
        min_value=0,
        decimal_places=2,
        initial=0,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 300000"})
    )
    down_payment_pct = forms.DecimalField(
        label="Down Payment (%)",
        min_value=0,
        max_value=100,
        decimal_places=2,
        initial=20,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 10"})
    )
    mortgage_apr = forms.DecimalField(
        label="Mortgage APR (%)",
        min_value=0,
        max_value=100,
        decimal_places=2,
        initial=3,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 5"})
    )
    loan_term_years = forms.IntegerField(
        label="Loan Term (Years)",
        min_value=1,
        initial=30,
        required=True,
        widget=forms.NumberInput(attrs={"placeholder": "e.g. 30"})
    )
