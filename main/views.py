from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from .forms import EmailLoginForm, CustomRegisterForm
from django import forms
import json
from .models import DebtCalculation
from decimal import Decimal, InvalidOperation
from django.forms import formset_factory, BaseFormSet
from django.shortcuts import render
from .utils import calcGains
import json
from django.contrib.auth.views import LogoutView
from django.http import HttpResponseNotAllowed


class SafeLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.method != "GET":
            return HttpResponseNotAllowed(['GET'])
        return super().dispatch(request, *args, **kwargs)



User = get_user_model()

def landing(request):
    return render(request, 'main/landing.html', {'APPNAME': 'Elite 5'})

def login_view(request):
    if request.method == 'POST':
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('landing')
    else:
        form = EmailLoginForm()
    return render(request, 'main/login.html', {'form': form, 'APPNAME': 'Elite 5'})

def register(request):
    if request.method == "POST":
        form = CustomRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('landing')
    else:
        form = CustomRegisterForm()
    return render(request, 'main/register.html', {'form': form, 'APPNAME': 'Elite 5'})

def about(request):
    team_members = [
        {'name': 'Anthony', 'bio': 'SupremeLeader', 'role': 'Project Manager', 'image': 'team/Anthony.jpg'},
        {'name': 'Francisco', 'bio': 'Senior at DePaul studying Computer Science & Mathematics.', 'role': 'Presentation Manager', 'image': 'team/Francisco.jpg'},
        {'name': 'Ish', 'bio': 'Junior at DePaul studying Computer Science.', 'role': 'Design Manager', 'image': 'team/Ish.jpg'},
        {'name': 'Chris', 'bio': 'Senior at DePaul studying Computer Science.', 'role': 'Requirements Manager', 'image': 'team/Chris.jpg'},
        {'name': 'Abdurrahman', 'bio': 'Senior at DePaul and future Software Engineer.', 'role': 'Project Tester', 'image': 'team/Abdurrahman.jpg'},
    ]
    return render(request, 'main/About.html', {'team_members': team_members, 'APPNAME': 'Elite 5'})

#@login_required
#def dashboard_view(request):
    #return render(request, 'main/dashboard.html')
class LoanForm(forms.Form):
    name = forms.CharField(label="Loan Name", required=True)
    balance = forms.DecimalField(label="Balance ($)", min_value=0)
    monthly_payment = forms.DecimalField(label="Monthly Payment ($)", min_value=0)
    interest_rate = forms.DecimalField(label="Annual Interest Rate (%)", min_value=0)

LoanFormSet = formset_factory(LoanForm, extra=1, can_delete=True)

def snowball_calculator(request):
    result = None
    formset = LoanFormSet(request.POST or None)

    strategy = request.POST.get('strategy', 'smallest_balance')
    raw_extra = request.POST.get('extra_payment', '').strip()
    try:
        extra_payment = Decimal(raw_extra) if raw_extra else Decimal('0')
    except InvalidOperation:
        extra_payment = Decimal('0')

    if request.method == 'POST' and formset.is_valid():
        loans = []
        for form in formset:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                cd = form.cleaned_data
                loans.append({
                    'name': cd['name'],
                    'balance': cd['balance'],
                    'monthly_payment': cd['monthly_payment'],
                    'monthly_rate': Decimal(cd['interest_rate']) / 100 / 12,
                    'interest_rate': cd['interest_rate'],
                })

        total_balance = sum(loan['balance'] for loan in loans)
        total_payment = Decimal('0')
        total_interest_paid = Decimal('0')
        chart_data = []
        months = 0

        base_total_payment = sum(l['monthly_payment'] for l in loans)

        while any(loan['balance'] > 0 for loan in loans) and months < 600:
            available_payment = base_total_payment + extra_payment

            # Apply interest
            for loan in loans:
                if loan['balance'] > 0:
                    interest = loan['balance'] * loan['monthly_rate']
                    loan['balance'] += interest
                    total_interest_paid += interest

            # Apply minimum payments
            for loan in loans:
                if loan['balance'] > 0:
                    payment = min(loan['monthly_payment'], loan['balance'])
                    loan['balance'] -= payment
                    total_payment += payment
                    available_payment -= payment

            # Apply remaining payment (snowball)
            unpaid_loans = [l for l in loans if l['balance'] > 0]
            if not unpaid_loans:
                break

            if strategy == 'highest_interest':
                target_loan = max(unpaid_loans, key=lambda l: l['monthly_rate'])
            elif strategy == 'fewest_payments':
                target_loan = min(unpaid_loans, key=lambda l: l['balance'] / l['monthly_payment'])
            else:
                target_loan = min(unpaid_loans, key=lambda l: l['balance'])

            if available_payment > 0:
                extra_to_apply = min(available_payment, target_loan['balance'])
                target_loan['balance'] -= extra_to_apply
                total_payment += extra_to_apply

            chart_data.append(round(sum(l['balance'] for l in loans), 2))
            months += 1

        result = {
            'months': months,
            'data_json': json.dumps([float(x) for x in chart_data]),
            'total_paid': round(total_payment, 2),
            'total_interest': round(total_interest_paid, 2),
        }

        loan_summary = "; ".join(
            f"{l['name']} (${l['balance']:.2f} at {l['interest_rate']}%)" for l in loans
        )

        DebtCalculation.objects.create(
            user=request.user,
            months_to_freedom=months,
            total_balance=total_balance,
            total_payment=total_payment,
            total_interest=total_interest_paid,
            loan_summary=loan_summary
        )

    return render(request, 'main/snowball_calculator.html', {
        'formset': formset,
        'result': result
    })

@login_required
def dashboard_view(request):
    history = DebtCalculation.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/dashboard.html', {'history': history})



def calculator_401k(request):
    context = {}

    if request.method == 'POST':
        try:
            year_of_retirement = int(request.POST.get("year_of_retirement"))
            init_deposit = float(request.POST.get("init_deposit"))
            salary = float(request.POST.get("salary"))
            salary_growth = float(request.POST.get("salary_growth_percent")) / 100
            contribution = float(request.POST.get("contribution_percent")) / 100
            match = float(request.POST.get("employer_match_percent")) / 100
            yield_rate = float(request.POST.get("annual_yield")) / 100

            total, growth_data = calcGains(init_deposit, year_of_retirement, salary, salary_growth, contribution, match, yield_rate)

            context = {
                "result": {
                    "projected_balance": total,
                    "data_json": json.dumps(growth_data),
                },
                "year_of_retirement": year_of_retirement,
                "init_deposit": init_deposit,
                "salary": salary,
                "salary_growth_percent": salary_growth * 100,
                "contribution_percent": contribution * 100,
                "employer_match_percent": match * 100,
                "annual_yield": yield_rate * 100,
            }
        except Exception as e:
            context["error"] = f"Error processing form: {e}"

    return render(request, "main/401k_calculator.html", context)