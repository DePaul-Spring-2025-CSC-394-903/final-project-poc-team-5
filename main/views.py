from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from .forms import EmailLoginForm, CustomRegisterForm, MainPaymentForm
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
    main_form = MainPaymentForm(request.POST or None)
    base_total_payment = Decimal('0')

    if request.method == 'POST' and formset.is_valid() and main_form.is_valid():
        strategy = main_form.cleaned_data.get('strategy', 'snowball')
        extra_payment = main_form.cleaned_data.get('additional_payment', Decimal('0'))

        loans = []
        for form in formset:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                cd = form.cleaned_data
                #oans.append({
                    #name': cd['name'],
                    #balance': cd['balance'],
                    #monthly_payment': cd['monthly_payment'],
                    #monthly_rate': Decimal(cd['interest_rate']) / 100 / 12,
                    #interest_rate': cd['interest_rate'],
                #)
                loans.append({
                    'name': cd['name'],
                    'initial_balance': cd['balance'],  # <-- NEW
                    'balance': cd['balance'],
                    'monthly_payment': cd['monthly_payment'],
                    'monthly_rate': Decimal(cd['interest_rate']) / 100 / 12,
                    'interest_rate': cd['interest_rate'],
                })

        # Calculate baseline interest for comparison (minimum payments only)
        baseline_loans = [loan.copy() for loan in loans]
        baseline_interest = Decimal('0')
        for _ in range(240):  # Max 20 years of months
            if all(l['balance'] <= 0 for l in baseline_loans):
                break
            for l in baseline_loans:
                if l['balance'] > 0:
                    interest = l['balance'] * l['monthly_rate']
                    l['balance'] += interest
                    baseline_interest += interest
                    payment = min(l['monthly_payment'], l['balance'])
                    l['balance'] -= payment

        total_balance = sum(l['balance'] for l in loans)
        total_payment = Decimal('0')
        total_interest = Decimal('0')
        months = 0
        chart_data = []

        base_total_payment = sum(l['monthly_payment'] for l in loans)

        while any(l['balance'] > 0 for l in loans) and months < 240:
            available = base_total_payment + extra_payment

            # Apply interest
            for loan in loans:
                if loan['balance'] > 0:
                    #interest = loan['balance'] * loan['monthly_rate']
                    interest = round(loan['balance'] * loan['monthly_rate'], 2)
                    loan['balance'] += interest
                    total_interest += interest

            # Apply minimum payments
            for loan in loans:
                if loan['balance'] > 0:
                    payment = min(loan['monthly_payment'], loan['balance'], available)
                    loan['balance'] -= payment
                    total_payment += payment
                    available -= payment

            # Sort strategy
            unpaid = [l for l in loans if l['balance'] > 0]
            if strategy == 'avalanche':
                unpaid.sort(key=lambda l: (-l['monthly_rate'], l['balance']))
            elif strategy == 'fewest_payments':
                unpaid.sort(key=lambda l: l['balance'] / max(l['monthly_payment'], Decimal('0.01')))
            else:
                unpaid.sort(key=lambda l: l['balance'])

            # Apply remaining to target
            if unpaid and available > 0:
                extra = min(unpaid[0]['balance'], available)
                unpaid[0]['balance'] -= extra
                total_payment += extra

            chart_data.append(float(sum(l['balance'] for l in loans)))
            months += 1

        result = {
            'months': months,
            'data_json': json.dumps(chart_data),
            'total_paid': round(total_payment, 2),
            'total_interest': round(total_interest, 2),
            'baseline_interest': round(baseline_interest, 2),
            'interest_saved': round(baseline_interest - total_interest, 2),
            'strategy_used': strategy,
        }

        #oan_summary = "; ".join(
            #"{l['name']} (${l['balance']:.2f} at {l['interest_rate']}%)" for l in loans
        #
        loan_summary = f"Strategy: {strategy.title()} | " + "; ".join(
            f"{l['name']} (Initial: ${l['initial_balance']:.2f}, Rate: {l['interest_rate']}%)"
            for l in loans
        )

        DebtCalculation.objects.create(
            user=request.user,
            months_to_freedom=months,
            total_balance=total_balance,
            total_payment=total_payment,
            total_interest=total_interest,
            loan_summary=loan_summary
        )

    return render(request, 'main/snowball_calculator.html', {
        'formset': formset,
        'main_form': main_form,
        'result': result,
        'total_monthly_payment': base_total_payment,
    })

@login_required
def dashboard_view(request):
    history = DebtCalculation.objects.filter(user=request.user).order_by('-created_at')[:3]
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

@login_required
def budgeting_tool(request):
    context = {
        'income': '',
        'result': None,
        'labels': json.dumps([
            'Housing', 'Food', 'Utilities', 'Transportation',
            'Healthcare', 'Savings', 'Debt', 'Entertainment'
        ]),
        'colors': json.dumps([
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#C9CBCF', '#6FCF97'
        ]),
        'allocations': None
    }

    if request.method == 'POST':
        try:
            income = float(request.POST.get('income'))
            ratios = [0.25, 0.1, 0.05, 0.2, 0.1, 0.1, 0.1, 0.1]
            allocations = [round(income * r, 2) for r in ratios]
            context['income'] = income
            context['result'] = json.dumps(allocations)
            context['allocations'] = zip(
                ['Housing', 'Food', 'Utilities', 'Transportation',
                 'Healthcare', 'Savings', 'Debt', 'Entertainment'],
                allocations,
                ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                 '#9966FF', '#FF9F40', '#C9CBCF', '#6FCF97']
            )
        except (ValueError, TypeError):
            context['error'] = "Invalid input. Please enter a numeric income."

    return render(request, 'main/budgeting_tool.html', context)
