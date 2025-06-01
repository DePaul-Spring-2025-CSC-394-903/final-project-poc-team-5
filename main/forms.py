from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.forms import formset_factory
from datetime import date

User = get_user_model()

class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("Invalid email or password")

        self.user = authenticate(username=user.username, password=password)
        if self.user is None:
            raise forms.ValidationError("Invalid email or password")
        return cleaned_data

    def get_user(self):
        return self.user

class CustomRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email
    
class LoanForm(forms.Form):
    balance = forms.DecimalField(label="Balance ($)", min_value=0, decimal_places=2)
    interest_rate = forms.DecimalField(label="Annual Interest Rate (%)", min_value=0, max_value=100, decimal_places=2)

LoanFormSet = formset_factory(LoanForm, extra=2)

STRATEGY_CHOICES = [
    ('snowball', 'Debt with smallest balance'),
    ('avalanche', 'Debt with highest interest rate'),
    ('fewest_payments', 'Debt with fewest payments left'),
]

class MainPaymentForm(forms.Form):
    #monthly_payment = forms.DecimalField(
        #label="Total Monthly Payment", min_value=0, decimal_places=2,
        #widget=forms.NumberInput(attrs={'type': 'number', 'step': '0.01'})
    #)

    additional_payment = forms.DecimalField(
        label="Additional Payment ($)", min_value=0, initial=0, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'type': 'number', 'step': '0.01', 'min': '0'
        })
    )

    strategy = forms.ChoiceField(
        label="Start Payoff With",
        choices=STRATEGY_CHOICES,
        widget=forms.Select()
    )

class MortgageForm(forms.Form):
    home_price = forms.DecimalField(label="Home price", min_value=0)
    down_payment = forms.DecimalField(label="Down payment", min_value=0)
    interest_rate = forms.DecimalField(label="Interest rate (%)", min_value=0)
    loan_term = forms.IntegerField(label="Loan term (years)", min_value=1)
    #start_date = forms.DateField(label="Start date", widget=forms.DateInput(attrs={'type': 'month'})
    start_date = forms.CharField(label="Start date (MM/YYYY)", widget=forms.TextInput(attrs={'type': 'month'}))