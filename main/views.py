from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.http import JsonResponse
from .forms import EmailLoginForm, CustomRegisterForm, MainPaymentForm, MortgageForm
from django import forms
import json
from .models import DebtCalculation
from decimal import Decimal, InvalidOperation
from django.forms import formset_factory, BaseFormSet
from .utils import calcGains, calculate_take_home, generate_amortization_schedule
from django.contrib.auth.views import LogoutView
from django.http import HttpResponseNotAllowed
from .models import RetirementCalculation
from datetime import datetime
from django.http import HttpResponseRedirect
from django.urls import reverse
from .tax_data import federal_tax_brackets, state_tax_brackets_2025
import math
from .models import SavingsCalculation
from .models import MortgageCalculation
from .models import TakeHomeCalculation
from .models import BudgetCalculation
from .forms import MergeForm, LoanFormSet
from .forms import (
    EmailLoginForm,
    CustomRegisterForm,
    LoanFormSet,
    MainPaymentForm,
    MortgageForm,
    MergeForm,
)
from datetime import datetime, date, timedelta      
from math import ceil




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

@login_required
def calculator_info_view(request):
    return render(request, "main/calculator_info.html")






from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from .forms import MainPaymentForm
from .models import DebtCalculation
from .views import LoanFormSet
import json

def snowball_calculator(request):
    result = None
    base_total_payment = Decimal('0')

    load_id = request.GET.get('load')
    initial_data = None
    strategy_initial = 'snowball'
    extra_payment_initial = Decimal('0')

    if load_id:
        try:
            calc = DebtCalculation.objects.get(pk=load_id, user=request.user)
            initial_data = [{
                'name': loan['name'],
                'balance': loan['initial_balance'],
                'monthly_payment': loan['monthly_payment'],
                'interest_rate': loan['interest_rate'],
            } for loan in calc.loan_data]

            strategy_initial = calc.strategy
            extra_payment_initial = calc.extra_payment
        except DebtCalculation.DoesNotExist:
            pass

    if request.method == 'POST':
        formset = LoanFormSet(request.POST)
        main_form = MainPaymentForm(request.POST)
    else:
        formset = LoanFormSet(initial=initial_data)
        main_form = MainPaymentForm(initial={
            'strategy': strategy_initial,
            'additional_payment': extra_payment_initial
        })

    if request.method == 'POST' and formset.is_valid() and main_form.is_valid():
        strategy = main_form.cleaned_data.get('strategy', 'snowball')
        extra_payment = main_form.cleaned_data.get('additional_payment', Decimal('0'))
        loans = []

        for form in formset:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                cd = form.cleaned_data
                loans.append({
                    'name': cd['name'],
                    'initial_balance': cd['balance'],
                    'balance': cd['balance'],
                    'monthly_payment': cd['monthly_payment'],
                    'monthly_rate': Decimal(cd['interest_rate']) / 100 / 12,
                    'interest_rate': cd['interest_rate'],
                })

        baseline_loans = [l.copy() for l in loans]
        baseline_interest = Decimal('0')
        for _ in range(240):
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
        monthly_breakdown = []

        base_total_payment = sum(l['monthly_payment'] for l in loans)

        while any(l['balance'] > 0 for l in loans) and months < 240:
            available = base_total_payment + extra_payment

            for loan in loans:
                if loan['balance'] > 0:
                    interest = round(loan['balance'] * loan['monthly_rate'], 2)
                    loan['balance'] += interest
                    total_interest += interest

            for loan in loans:
                if loan['balance'] > 0:
                    payment = min(loan['monthly_payment'], loan['balance'], available)
                    loan['balance'] -= payment
                    total_payment += payment
                    available -= payment

            unpaid = [l for l in loans if l['balance'] > 0]
            if strategy == 'avalanche':
                unpaid.sort(key=lambda l: (-l['monthly_rate'], l['balance']))
            elif strategy == 'fewest_payments':
                unpaid.sort(key=lambda l: l['balance'] / max(l['monthly_payment'], Decimal('0.01')))
            else:
                unpaid.sort(key=lambda l: l['balance'])

            if unpaid and available > 0:
                extra = min(unpaid[0]['balance'], available)
                unpaid[0]['balance'] -= extra
                total_payment += extra

            monthly_breakdown.append({
                "month": months + 1,                                        # ➜ human-friendly
                "balances": [float(round(l["balance"], 2)) for l in loans],
                "total_balance": float(round(sum(l["balance"] for l in loans), 2)),
                "available": float(round(available, 2))
                })

            chart_data.append(float(sum(l['balance'] for l in loans)))
            months += 1

          

        result = {
            'months': months,
            'data_json': json.dumps(chart_data),
            'total_paid': float(round(total_payment, 2)),
            'total_interest': float(round(total_interest, 2)),
            'baseline_interest': float(round(baseline_interest, 2)),
            'interest_saved': float(round(baseline_interest - total_interest, 2)),
            'strategy_used': strategy,
        }
        loan_data_serialized = [
            {
                'name': l['name'],
                'initial_balance': float(l['initial_balance']),
                'balance': float(l['balance']),
                'monthly_payment': float(l['monthly_payment']),
                'monthly_rate': float(l['monthly_rate']),
                'interest_rate': float(l['interest_rate']),
            }
            for l in loans
        ]


        request.session['snowball_result'] = result
        request.session['snowball_monthly_breakdown'] = monthly_breakdown

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
            strategy=strategy,
            extra_payment=extra_payment,
            loan_summary=loan_summary,
            loan_data=loan_data_serialized
        )

        return redirect('snowball_result')

    return render(request, 'main/snowball_calculator.html', {
        'formset': formset,
        'main_form': main_form,
        'result': result,
        'total_monthly_payment': base_total_payment,
        #"schedule": amortization_schedule
    })

@login_required
def snowball_monthly_breakdown(request):
    breakdown = request.session.get('snowball_monthly_breakdown')
    if not breakdown:
        return redirect('snowball_calculator')
    return render(request, 'main/snowball_monthly_breakdown.html', {'breakdown': breakdown})


@login_required
@require_POST
def delete_calculation(request, pk):
    calc = get_object_or_404(DebtCalculation, pk=pk, user=request.user)
    calc.delete()
    return redirect('snowball_history')


@login_required
def snowball_history(request):
    calculations = DebtCalculation.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/snowball_history.html', {'calculations': calculations})


def snowball_result_view(request):
    result = request.session.get('snowball_result')
    if not result:
        return redirect('debt_calculator')

    return render(request, 'main/snowball_result.html', {'result': result})


@login_required
def dashboard_view(request):
    history = DebtCalculation.objects.filter(user=request.user).order_by('-created_at')[:3]

    has_result = 'snowball_result' in request.session
    has_401k_result = 'last_401k_result' in request.session

    context = {
    'has_result': 'snowball_result' in request.session,
    'has_401k_result': 'last_401k_result' in request.session,
    'has_budget_result': BudgetCalculation.objects.filter(user=request.user).exists(),
    'has_savings_result': SavingsCalculation.objects.filter(user=request.user).exists(),
    'has_take_home_result': TakeHomeCalculation.objects.filter(user=request.user).exists(),
    'has_mortgage_result': MortgageCalculation.objects.filter(user=request.user).exists(),
    'history': DebtCalculation.objects.filter(user=request.user).order_by('-created_at')[:3]
}

    return render(request, 'main/dashboard.html', context)




from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from decimal import Decimal
import json
from .models import RetirementCalculation
from .utils import calcGains

@login_required
def calculator_401k(request):
    context = {}

    def safe_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    if request.method == 'POST':
        try:
            current_age = int(request.POST.get("current_age", 30))
            retirement_age = int(request.POST.get("retirement_age", 65))
            init_deposit = safe_float(request.POST.get("init_deposit"))
            salary = safe_float(request.POST.get("salary"))
            salary_growth = safe_float(request.POST.get("salary_growth_percent")) / 100
            contribution = safe_float(request.POST.get("contribution_percent")) / 100
            match = safe_float(request.POST.get("employer_match_percent")) / 100
            match_limit = safe_float(request.POST.get("employer_match_limit_percent")) / 100
            yield_rate = safe_float(request.POST.get("annual_yield")) / 100

            total, growth_data, total_emp, total_em = calcGains(
                init_deposit,
                current_age,
                retirement_age,
                salary,
                salary_growth,
                contribution,
                match,
                match_limit,
                yield_rate
            )

            context["result"] = {
                "projected_balance": round(total, 2),
                "data_json": json.dumps(growth_data),
                "year_of_retirement": retirement_age
            }

            context.update({
                "current_age": current_age,
                "retirement_age": retirement_age,
                "init_deposit": init_deposit,
                "salary": salary,
                "salary_growth_percent": salary_growth * 100,
                "contribution_percent": contribution * 100,
                "employer_match_percent": match * 100,
                "employer_match_limit_percent": match_limit * 100,
                "annual_yield": yield_rate * 100
            })

            request.session["last_401k_result"] = context["result"]

            RetirementCalculation.objects.create(
                user=request.user,
                current_age=current_age,
                retirement_age=retirement_age,
                projected_balance=total,
                init_deposit=init_deposit,
                salary=salary,
                contribution=contribution * 100
            )

        except Exception as e:
            context["error"] = f"Error processing form: {e}"

    return render(request, "main/401k_calculator.html", context)




@login_required
def retirement_history(request):
    history = RetirementCalculation.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/401k_history.html', {'history': history})

@login_required
def retirement_result_view(request):
    result = request.session.get('last_401k_result')
    if not result:
        return redirect('calculator_401k')  # Fallback if nothing stored

    return render(request, 'main/401k_result.html', {'result': result})

@login_required
def delete_retirement_entry(request, pk):
    entry = get_object_or_404(RetirementCalculation, pk=pk, user=request.user)
    if request.method == "POST":
        entry.delete()
        return redirect('retirement_history')
    return render(request, 'main/confirm_delete.html', {'entry': entry})

@login_required
def edit_retirement_entry(request, pk):
    entry = get_object_or_404(RetirementCalculation, pk=pk, user=request.user)

    if request.method == "POST":
        try:
            current_age = int(request.POST.get("current_age"))
            retirement_age = int(request.POST.get("retirement_age"))
            init_deposit = float(request.POST.get("init_deposit"))
            salary = float(request.POST.get("salary"))
            salary_growth = float(request.POST.get("salary_growth_percent")) / 100
            contribution = float(request.POST.get("contribution_percent")) / 100
            employer_match = float(request.POST.get("employer_match_percent")) / 100
            employer_match_limit = float(request.POST.get("employer_match_limit")) / 100
            yield_rate = float(request.POST.get("annual_yield")) / 100

            # Run calculation again
            total, growth_data, emp_contrib, match_contrib = calcGains(
                init_deposit,
                current_age,
                retirement_age,
                salary,
                salary_growth,
                contribution,
                employer_match,
                employer_match_limit,
                yield_rate
            )

            # Update the DB entry
            entry.current_age = current_age
            entry.retirement_age = retirement_age
            entry.init_deposit = init_deposit
            entry.salary = salary
            entry.salary_growth = salary_growth * 100
            entry.contribution = contribution * 100
            entry.yield_rate = yield_rate * 100
            entry.total_employee_contrib = emp_contrib
            entry.total_employer_contrib = match_contrib
            entry.projected_balance = round(total, 2)

            entry.save()
            return redirect('retirement_history')

        except Exception as e:
            return render(request, 'main/edit_401k.html', {
                'entry': entry,
                'error': f"Error: {e}"
            })

    return render(request, 'main/edit_401k.html', {'entry': entry})


@login_required
def budgeting_tool(request):
    user = request.user
    session_income = request.session.get("fixed_income")

    selected_debt_id = request.POST.get("debt_selection")
    selected_401k_id = request.POST.get("retirement_selection")

    context = {
        'income': session_income or '',
        'result': None,
        'labels': json.dumps([
            'Housing', 'Food', 'Utilities', 'Transportation',
            'Healthcare', 'Savings', 'Debt', 'Entertainment'
        ]),
        'colors': json.dumps([
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
            '#9966FF', '#FF9F40', '#C9CBCF', '#6FCF97'
        ]),
        'allocations': None,
        'locked_income': bool(session_income),
        'debt_history': DebtCalculation.objects.filter(user=user).order_by('-created_at'),
        'retirement_history': RetirementCalculation.objects.filter(user=user).order_by('-created_at'),
        'selected_debt_id': selected_debt_id,
        'selected_401k_id': selected_401k_id
    }

    if request.method == 'POST':
        try:
            if not session_income:
                income = float(request.POST.get('income'))
                request.session['fixed_income'] = income
            else:
                income = float(session_income)

            
            snowball_monthly = 0
            if selected_debt_id:
                debt_entry = DebtCalculation.objects.filter(user=user, pk=selected_debt_id).first()
                if debt_entry:
                    snowball_monthly = float(debt_entry.total_payment) / float(debt_entry.months_to_freedom)

            
            retirement_monthly = 0
            if selected_401k_id:
                retirement_entry = RetirementCalculation.objects.filter(user=user, pk=selected_401k_id).first()
                if retirement_entry:
                    retirement_monthly = float(retirement_entry.salary) * (float(retirement_entry.contribution) / 100) / 12

            
            ratios = {
                "Housing": 0.25,
                "Food": 0.10,
                "Utilities": 0.05,
                "Transportation": 0.15,
                "Healthcare": 0.10,
                "Entertainment": 0.05
            }

            

            base_total = sum(ratios.values())
            remaining_income = max(0, income - (snowball_monthly + retirement_monthly))

            base_allocations = [round(remaining_income * ratios[cat], 2) for cat in ratios]

            savings = round(retirement_monthly, 2)
            debt = round(snowball_monthly, 2)

            final_allocations = base_allocations[:5] + [savings, debt, base_allocations[5]]

            BudgetCalculation.objects.create(
                user=request.user,
                monthly_income=income,
                total_expenses=sum(final_allocations),
                savings_goal=savings
            )


            context['income'] = income
            context['result'] = json.dumps(final_allocations)
            context['allocations'] = zip(
                ['Housing', 'Food', 'Utilities', 'Transportation',
                 'Healthcare', 'Savings', 'Debt', 'Entertainment'],
                final_allocations,
                ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                 '#9966FF', '#FF9F40', '#C9CBCF', '#6FCF97']
            )
        except (ValueError, TypeError) as e:
            context['error'] = f"Invalid input: {e}"

    return render(request, 'main/budgeting_tool.html', context)

@login_required
def budget_history(request):
    if request.user.is_authenticated:
        history = BudgetCalculation.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'main/budget_history.html', {'history': history})
    return redirect('login')

@login_required
def edit_budget_entry(request, pk):
    entry = get_object_or_404(BudgetCalculation, pk=pk, user=request.user)

    if request.method == 'POST':
        try:
            income = float(request.POST.get('monthly_income'))
            expenses = float(request.POST.get('total_expenses'))
            savings = float(request.POST.get('savings_goal'))

            entry.monthly_income = income
            entry.total_expenses = expenses
            entry.savings_goal = savings
            entry.save()

            return redirect('budget_history')
        except Exception as e:
            return render(request, 'main/edit_budget.html', {
                'entry': entry,
                'error': f"Error: {e}"
            })

    return render(request, 'main/edit_budget.html', {'entry': entry})

@login_required
@require_POST
def delete_budget_entry(request, pk):
    entry = get_object_or_404(BudgetCalculation, pk=pk, user=request.user)
    entry.delete()
    return redirect('budget_history')


@require_POST
@login_required
def reset_income(request):
    request.session.pop("fixed_income", None)
    return redirect('budgeting_tool')
    
@login_required    
def take_home_calculator(request):
    pay_periods = {
        "annual": 1,
        "monthly": 12,
        "semi_monthly": 24,
        "bi_weekly": 26,
        "weekly": 52
    }

    us_states = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
        "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "District of Columbia",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
        "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
        "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan",
        "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri", "MT": "Montana",
        "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
        "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota",
        "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
        "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
        "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
        "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
    }

    context = {"result": None, "states": us_states}

    if request.method == "POST":
        try:
            annual_income = float(request.POST.get("income"))
            status = request.POST.get("status", "single")
            state = request.POST.get("state", "Other")
            frequency = request.POST.get("pay_frequency", "annual")
            fed_allowances = int(request.POST.get("fed_allowances", 1))
            state_allowances = int(request.POST.get("state_allowances", 1))
            local_rate = float(request.POST.get("local_tax_rate", 0)) / 100
            pre_tax = float(request.POST.get("pre_tax", 0))
            post_tax = float(request.POST.get("post_tax", 0))

            periods = pay_periods.get(frequency, 1)
            per_period_income = annual_income / periods

            tax_data = calculate_take_home(
                annual_income,
                status,
                state,
                fed_allowances,
                state_allowances,
                local_rate,
                pre_tax,
                post_tax
            )
            TakeHomeCalculation.objects.create(
                user=request.user,
                income=annual_income,
                filing_status=status,
                state=state,
                frequency=frequency,
                take_home_annual=tax_data["take_home_pay"],
                take_home_per_period=tax_data["take_home_pay"] / periods
            )

            context["result"] = {
                "gross_income": round(per_period_income, 2),
                "federal_tax": round(tax_data["federal_tax"] / periods, 2),
                "state_tax": round(tax_data["state_tax"] / periods, 2),
                "fica_tax": round(tax_data["fica_tax"] / periods, 2),
                "local_tax": round(tax_data["local_tax"] / periods, 2),
                "total_tax": round(tax_data["total_tax"] / periods, 2),
                "take_home_pay": round(tax_data["take_home_pay"] / periods, 2),
                "annual_take_home": tax_data["take_home_pay"],
                "annual_gross": annual_income,
                "pay_frequency": frequency.replace("_", " ").title()
            }

            context.update({
                "income": annual_income,
                "status": status,
                "state": state,
                "pay_frequency": frequency,
                "fed_allowances": fed_allowances,
                "state_allowances": state_allowances,
                "local_tax_rate": local_rate * 100,
                "pre_tax": pre_tax,
                "post_tax": post_tax
            })

        except Exception as e:
            context["error"] = f"Invalid input: {e}"

    return render(request, "main/take_home_calculator.html", context)

@login_required
def take_home_history(request):
    if request.user.is_authenticated:
        history = TakeHomeCalculation.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'main/take_home_history.html', {'history': history})
    return redirect('login')

@login_required
def edit_take_home_entry(request, pk):
    entry = get_object_or_404(TakeHomeCalculation, pk=pk, user=request.user)

    if request.method == 'POST':
        try:
            entry.income = float(request.POST.get("income"))
            entry.filing_status = request.POST.get("filing_status")
            entry.state = request.POST.get("state")
            entry.frequency = request.POST.get("frequency")

            # Recalculate take-home
            periods = {
                "annual": 1, "monthly": 12, "semi_monthly": 24,
                "bi_weekly": 26, "weekly": 52
            }[entry.frequency]
            tax_result = calculate_take_home(
                entry.income, entry.filing_status, entry.state, 1, 1, 0, 0, 0
            )

            entry.take_home_annual = tax_result["take_home_pay"]
            entry.take_home_per_period = tax_result["take_home_pay"] / periods
            entry.save()
            return redirect('take_home_history')

        except Exception as e:
            return render(request, 'main/edit_take_home.html', {'entry': entry, 'error': f"Error: {e}"})

    return render(request, 'main/edit_take_home.html', {'entry': entry})


@login_required
@require_POST
def delete_take_home_entry(request, pk):
    entry = get_object_or_404(TakeHomeCalculation, pk=pk, user=request.user)
    entry.delete()
    return redirect('take_home_history')


def calculate_savings_growth(starting_balance, years, interest_rate, compound_frequency, contribution, contribution_frequency, goal=None):
    months = years * 12
    balance = starting_balance
    history = []
    goal_months = None

    for month in range(1, months + 1):
        if compound_frequency == 'monthly':
            balance *= (1 + (interest_rate / 100) / 12)
        elif compound_frequency == 'annually' and month % 12 == 0:
            balance *= (1 + (interest_rate / 100))

        if contribution_frequency == 'monthly':
            balance += contribution
        elif contribution_frequency == 'annually' and month % 12 == 0:
            balance += contribution

        history.append(round(balance, 2))

        if goal is not None and goal_months is None and balance >= goal:
            goal_months = month

    return round(balance, 2), history, goal_months


@login_required
def savings_calculator(request):
    result = None
    error = None

    if request.method == "POST":
        try:
            starting_balance = float(request.POST.get("starting_balance", "") or 0)
            years = int(request.POST.get("years", "") or 0)
            interest_rate = float(request.POST.get("interest_rate", "") or 0)
            compound_frequency = request.POST.get("compound_frequency", "monthly")
            contribution_amount = float(request.POST.get("contribution_amount", "") or 0)
            contribution_frequency = request.POST.get("contribution_frequency", "monthly")
            goal_input = request.POST.get("goal", "").strip()
            goal = float(goal_input) if goal_input else None

            if years <= 0 or interest_rate < 0 or starting_balance < 0:
                raise ValueError("Please enter non‐negative numbers for balance, years, and interest.")

            monthly_rate = (interest_rate / 100) / 12
            if contribution_frequency == "monthly":
                contrib_interval = 1
            else:
                contrib_interval = 12

            total_months = years * 12
            balance = starting_balance
            monthly_balances = []
            goal_months = None

            for month in range(1, total_months + 1):
                balance *= (1 + monthly_rate)
                if month % contrib_interval == 0:
                    balance += contribution_amount
                monthly_balances.append(round(balance, 2))
                if goal is not None and goal_months is None and balance >= goal:
                    goal_months = month

            final_balance = round(balance, 2)
            data_json = json.dumps(monthly_balances)

            result = {
                "final_balance": final_balance,
                "goal_months": goal_months,
                "data_json": data_json
            }
            SavingsCalculation.objects.create(
                user                 = request.user,
                initial_amount       = starting_balance,
                monthly_contribution = contribution_amount,
                interest_rate        = interest_rate,
                duration_years       = years,
                total_saved          = final_balance,
    )

        except (ValueError, TypeError) as e:
            error = str(e)

    context = {
        "starting_balance": request.POST.get("starting_balance", "") if request.method == "POST" else "",
        "years": request.POST.get("years", "") if request.method == "POST" else "",
        "interest_rate": request.POST.get("interest_rate", "") if request.method == "POST" else "",
        "compound_frequency": request.POST.get("compound_frequency", "monthly") if request.method == "POST" else "monthly",
        "contribution_amount": request.POST.get("contribution_amount", "") if request.method == "POST" else "",
        "contribution_frequency": request.POST.get("contribution_frequency", "monthly") if request.method == "POST" else "monthly",
        "goal": request.POST.get("goal", "") if request.method == "POST" else "",
        "result": result,
        "error": error
    }

    return render(request, "main/savings_calculator.html", context)



@login_required
def savings_history(request):
    history = SavingsCalculation.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/savings_history.html', {'history': history})

@login_required
def edit_savings_entry(request, pk):
    entry = get_object_or_404(SavingsCalculation, pk=pk, user=request.user)

    if request.method == 'POST':
        try:
            entry.initial_amount = float(request.POST.get('initial_amount'))
            entry.monthly_contribution = float(request.POST.get('monthly_contribution'))
            entry.interest_rate = float(request.POST.get('interest_rate'))
            entry.duration_years = int(request.POST.get('duration_years'))

            # Recalculate
            final_balance, _, _ = calculate_savings_growth(
                entry.initial_amount,
                entry.duration_years,
                entry.interest_rate,
                'monthly',  # assume monthly compound
                entry.monthly_contribution,
                'monthly'   # assume monthly contribution
            )
            entry.total_saved = final_balance
            entry.save()
            return redirect('savings_history')
        except Exception as e:
            return render(request, 'main/edit_savings.html', {'entry': entry, 'error': f"Error: {e}"})

    return render(request, 'main/edit_savings.html', {'entry': entry})

@login_required
@require_POST
def delete_savings_entry(request, pk):
    entry = get_object_or_404(SavingsCalculation, pk=pk, user=request.user)
    entry.delete()
    return redirect('savings_history')

@login_required
def latest_savings_result(request):
    entry = (
        SavingsCalculation.objects
        .filter(user=request.user)
        .order_by("-created_at")
        .first()
    )
    if not entry:
        return redirect("savings_calculator")

    # --- rebuild series -------------------------------------------------
    months_total   = entry.duration_years * 12
    monthly_rate   = float(entry.interest_rate) / 100 / 12
    balance        = float(entry.initial_amount)
    series         = []

    for _ in range(1, months_total + 1):
        balance *= (1 + monthly_rate)
        balance += float(entry.monthly_contribution)
        series.append(round(balance, 2))

    labels         = [f"Month {i}" for i in range(1, months_total + 1)]
    final_balance  = series[-1]                           # up-to-date!
    total_contrib  = round(entry.monthly_contribution * months_total, 2)

    return render(
        request,
        "main/savings_result.html",                 # path below
        {
            "entry":          entry,          # raw DB row (if you still need it)
            "final_balance":  final_balance,  # fresh number for template
            "total_contrib":  total_contrib,
            "labels":  json.dumps(labels),
            "values":  json.dumps(series),
        },
    )

@login_required
def savings_result_view(request):
    # Retrieve the latest saved result ID from the session
    result_id = request.session.get('last_savings_result_id')
    if not result_id:
        return redirect('savings_calculator')  # Fallback if no saved result

    try:
        result = SavingsCalculation.objects.get(id=result_id, user=request.user)
    except SavingsCalculation.DoesNotExist:
        return redirect('savings_calculator')

    # Generate graph data like you do after form submission
    months = list(range(1, result.total_months + 1))
    balance = []
    current = result.initial_deposit
    monthly_contribution = result.monthly_contribution
    rate = result.annual_interest_rate / 100 / 12

    for _ in months:
        current = current * (1 + rate) + monthly_contribution
        balance.append(round(current, 2))

    context = {
        'result': result,
        'months': months,
        'balance': balance,
    }

    return render(request, 'main/savings_result.html', context)





def calculate_savings_graph_data(principal, years, rate, monthly_contrib):
    monthly_rate = rate / 100 / 12
    months = years * 12
    balance = principal
    values = []

    for m in range(0, months + 1, 12):
        balance = principal * ((1 + monthly_rate) ** m)
        for month in range(m):
            balance += monthly_contrib * ((1 + monthly_rate) ** (months - month))
        values.append(round(balance, 2))
    
    return values


@login_required
def mortgage_calculator(request):
    result = None
    amortization_schedule = None

    if request.method == 'POST':
        form = MortgageForm(request.POST)
        if form.is_valid():
            price = form.cleaned_data['home_price']
            down = form.cleaned_data.get('down_payment') or 0
            down_percent = form.cleaned_data.get('down_payment_percent') or 0
            rate = form.cleaned_data['interest_rate'] / 100 / 12
            years = form.cleaned_data['loan_term']

            # Fallback: if user left down_payment blank but entered a percentage
            if down == 0 and down_percent:
                down = price * (down_percent / 100)

            # Handle MM/YYYY input (type="month")
            raw_date = form.cleaned_data['start_date']
            try:
                start_date = datetime.strptime(raw_date, "%Y-%m")
            except ValueError:
                form.add_error('start_date', "Enter date in MM/YYYY format.")
                return render(request, "main/mortgage_calculator.html", {"form": form})

            principal = price - down
            n = years * 12

            try:
                monthly_payment = principal * (rate * (1 + rate) ** n) / ((1 + rate) ** n - 1)
            except ZeroDivisionError:
                monthly_payment = principal / n

            total_payment = monthly_payment * n
            total_interest = total_payment - principal

            payoff_date = start_date.replace(year=start_date.year + years)

            result = {
                'monthly_payment': round(monthly_payment, 2),
                'total_interest': round(total_interest, 2),
                'total_payment': round(total_payment, 2),
                'principal': round(principal, 2),
                'payoff_date': payoff_date.strftime("%m / %Y")
            }
            MortgageCalculation.objects.create(
                user=request.user,
                home_price=price,
                down_payment=down,
                interest_rate=form.cleaned_data['interest_rate'],
                term_years=years,
                monthly_payment=round(monthly_payment, 2),
                total_payment=round(total_payment, 2),
                total_interest=round(total_interest, 2),
                payoff_date=payoff_date.strftime("%m / %Y")
            )

            amortization_schedule = generate_amortization_schedule(
                principal=Decimal(principal),
                annual_rate=Decimal(form.cleaned_data['interest_rate']),
                years=years,
                start_date=start_date
)
    else:
        form = MortgageForm()

    return render(request, "main/mortgage_calculator.html", {"form": form, "result": result,  "schedule": amortization_schedule})

@login_required
def mortgage_history(request):
    if request.user.is_authenticated:
        history = MortgageCalculation.objects.filter(user=request.user).order_by('-created_at')
        return render(request, 'main/mortgage_history.html', {'history': history})
    return redirect('login')

@login_required
def edit_mortgage_entry(request, pk):
    entry = get_object_or_404(MortgageCalculation, pk=pk, user=request.user)

    if request.method == 'POST':
        try:
            home_price = float(request.POST.get("home_price"))
            down_payment = float(request.POST.get("down_payment"))
            interest_rate = float(request.POST.get("interest_rate"))
            term_years = int(request.POST.get("term_years"))

            principal = home_price - down_payment
            monthly_rate = interest_rate / 100 / 12
            months = term_years * 12

            monthly_payment = (
                principal * monthly_rate / (1 - (1 + monthly_rate) ** -months)
            )
            total_payment = monthly_payment * months
            total_interest = total_payment - principal

            entry.home_price = home_price
            entry.down_payment = down_payment
            entry.interest_rate = interest_rate
            entry.term_years = term_years
            entry.monthly_payment = round(monthly_payment, 2)
            entry.total_payment = round(total_payment, 2)
            entry.total_interest = round(total_interest, 2)
            entry.payoff_date = (timezone.now() + timedelta(days=30 * months)).strftime("%B %Y")

            entry.save()
            return redirect('mortgage_history')

        except Exception as e:
            return render(request, 'main/edit_mortgage.html', {'entry': entry, 'error': str(e)})

    return render(request, 'main/edit_mortgage.html', {'entry': entry})


@login_required
@require_POST
def delete_mortgage_entry(request, pk):
    entry = get_object_or_404(MortgageCalculation, pk=pk, user=request.user)
    entry.delete()
    return redirect('mortgage_history')

@login_required
def latest_mortgage_result(request):
    latest_entry = (
        MortgageCalculation.objects.filter(user=request.user)
        .order_by('-created_at')
        .first()
    )
    return render(request, 'main/latest_mortgage_result.html', {'entry': latest_entry})



@login_required
def latest_take_home_result(request):
    latest_entry = TakeHomeCalculation.objects.filter(user=request.user).order_by('-created_at').first()
    if not latest_entry:
        return redirect('take_home_calculator')  # fallback if none
    return render(request, 'main/take_home_result.html', {'result': latest_entry})



@login_required
def latest_budget_result(request):
    entry = (
        BudgetCalculation.objects
        .filter(user=request.user)
        .order_by("-created_at")
        .first()
    )
    if not entry:
        return redirect("budgeting_tool")

    labels = [
        "Housing","Food","Utilities","Transportation",
        "Healthcare","Savings","Debt","Entertainment"
    ]
    colors = [
        "#FF6384","#36A2EB","#FFCE56","#4BC0C0",
        "#9966FF","#FF9F40","#C9CBCF","#6FCF97"
    ]

    # ---------- math (all cast to float) ----------
    base_ratios          = [0.25, 0.10, 0.05, 0.15, 0.10]
    variable_pool        = float(entry.monthly_income - entry.savings_goal)
    fixed_slices_5       = [round(variable_pool * r, 2) for r in base_ratios]

    savings_slice        = float(entry.savings_goal)
    debt_slice           = float(entry.total_expenses) - savings_slice
    entertainment_slice  = round(variable_pool * 0.05, 2)

    values = fixed_slices_5 + [savings_slice, debt_slice, entertainment_slice]

    return render(
        request,
        "main/budget_result.html",
        {
            "result": entry,
            "labels": json.dumps(labels),
            "colors": json.dumps(colors),
            "values": json.dumps(values),
        },
    )



# main/views.py

@login_required
def merge_calculator(request):
    """
    GET  – render blank MergeForm + LoanFormSet
    POST – validate, run all calcs, show consolidated result
    """
    result, error = {}, None

    if request.method == "POST":
        form          = MergeForm(request.POST)
        loan_formset  = LoanFormSet(request.POST, prefix="loans")

        if form.is_valid() and loan_formset.is_valid():
            cd = form.cleaned_data

            # ───────────────────── 1) TAKE-HOME PAY ──────────────────────
            annual_income = float(cd["annual_salary"])
            status        = cd["filing_status"]
            state         = cd["state"]
            frequency     = cd["pay_frequency"]

            tax_data = calculate_take_home(     # your helper’s signature
                annual_income,
                status,
                state,
                fed_allowances = 1,
                state_allowances = 1,
                local_rate = 0,
                pre_tax = 0,
                post_tax = 0,
            )

            # convert to monthly net-estimate
            freq_to_month = {"annual": 1/12, "monthly": 1, "bi_weekly": 26/12}
            monthly_net   = round(tax_data["take_home_pay"] * freq_to_month[frequency], 2)

            result["take_home"] = {
                "net_per_period"   : round(tax_data["take_home_pay"], 2),
                "annual_take_home" : round(tax_data["take_home_pay"], 2 if frequency=="annual" else 0),
                "pay_frequency"    : frequency,
            }

            TakeHomeCalculation.objects.create(
                user=request.user,
                income              = annual_income,
                filing_status       = status,
                state               = state,
                frequency           = frequency,
                take_home_annual    = tax_data["take_home_pay"],
                take_home_per_period= tax_data["take_home_pay"],
            )

            # ───────────────────── 2) 401(k)  ────────────────────────────
            current_age    = cd["current_age"]
            retirement_age = cd["retirement_age"]
            init_401k      = float(cd["init_401k_deposit"])
            contrib_pct    = float(cd["contribution_pct"]) / 100      # 0 → 1

            #              init,      age,     retire,  salary,  salary_growth,
            #              contr, match, match_limit, yield_rate
            total_401k, growth_401k, _, _ = calcGains(
            init_401k,
            current_age,
            retirement_age,
            annual_income,
            0,             # salary growth assumption
            contrib_pct,   # employee contribution
            0,             # employer match %
            0,             # match limit %
            0.06           # annual yield (6 %)
            )

            result["retirement"] = {
                "projected_balance" : round(total_401k, 2),
                "data_json"         : json.dumps(growth_401k),
                "years_to_retire"   : retirement_age - current_age,
                "annual_contribution": round(annual_income * contrib_pct, 2),
            }

            RetirementCalculation.objects.create(
                user              = request.user,
                current_age       = current_age,
                retirement_age    = retirement_age,
                init_deposit      = init_401k,
                salary            = annual_income,
                contribution      = contrib_pct * 100,
                projected_balance = round(total_401k, 2),
            )

            # ───────────────────── 3) SAVINGS  ───────────────────────────
            sb, sy  = float(cd["savings_initial"]), int(cd["savings_years"])
            si, sc  = float(cd["savings_interest"]), float(cd["savings_contribution"])
            sg      = float(cd["savings_goal"] or 0)

            bal, m_balances, goal_mo = sb, [], None
            for m in range(1, sy*12 + 1):
                bal *= 1 + (si/100)/12
                bal += sc
                m_balances.append(round(bal, 2))
                if sg and goal_mo is None and bal >= sg:
                    goal_mo = m

            result["savings"] = {
                "final_balance": round(bal, 2),
                "goal_months"  : goal_mo,
                "data_json"    : json.dumps(m_balances),
            }

            SavingsCalculation.objects.create(
                user                = request.user,
                initial_amount      = sb,
                monthly_contribution= sc,
                interest_rate       = si,
                duration_years      = sy,
                total_saved         = round(bal, 2),
            )

            # ───────────────────── 4) MORTGAGE  ──────────────────────────
            price  = float(cd["home_price"])
            dp_pct = float(cd["down_payment_pct"]) / 100
            apr    = float(cd["mortgage_apr"])
            term_y = int(cd["loan_term_years"])

            principal   = price * (1 - dp_pct)
            m_rate      = (apr/100)/12
            n           = term_y * 12
            m_payment   = principal * (m_rate*(1+m_rate)**n)/((1+m_rate)**n - 1) if m_rate else principal/n
            payoff      = date.today() + timedelta(days=term_y*365)

            result["mortgage"] = {
                "monthly_payment": round(m_payment, 2),
                "total_interest" : round(m_payment*n - principal, 2),
                "total_payment"  : round(m_payment*n, 2),
                "payoff_date"    : payoff.strftime("%Y-%m"),
            }

            MortgageCalculation.objects.create(
                user            = request.user,
                home_price      = price,
                down_payment    = price*dp_pct,
                interest_rate   = apr,
                term_years      = term_y,
                monthly_payment = round(m_payment, 2),
                total_payment   = round(m_payment*n, 2),
                total_interest  = round(m_payment*n - principal, 2),
                payoff_date     = payoff.strftime("%Y-%m"),
            )

            # ───────────────────── 5) DEBT / SNOWBALL ────────────────────
            loans = []
            for lf in loan_formset:
                if lf.cleaned_data and not lf.cleaned_data.get("DELETE", False):
                    d = lf.cleaned_data
                    loans.append({
                        "name"            : d["name"],
                        "initial_balance" : float(d["balance"]),
                        "balance"         : float(d["balance"]),
                        "monthly_payment" : float(d["monthly_payment"]),
                        "monthly_rate"    : (float(d["interest_rate"])/100)/12,
                        "interest_rate"   : float(d["interest_rate"]),
                    })

            if not loans:
                form.add_error(None, "Please add at least one loan.")
                error = "Please add at least one loan."
            else:
                total_balance  = sum(l["balance"] for l in loans)
                total_payment  = 0
                total_interest = 0
                months         = 0
                hist           = []

                while any(l["balance"] > 0 for l in loans) and months < 240:
                    # accrue interest
                    for l in loans:
                        if l["balance"] > 0:
                            intr = l["balance"] * l["monthly_rate"]
                            l["balance"] += intr
                            total_interest += intr
                    # pay mins
                    for l in loans:
                        if l["balance"] > 0:
                            pay = min(l["monthly_payment"], l["balance"])
                            l["balance"] -= pay
                            total_payment += pay
                    # snowball extra toward smallest balance
                    unpaid = [l for l in loans if l["balance"] > 0]
                    unpaid.sort(key=lambda x: x["balance"])
                    if len(unpaid) > 1:
                        extra = min(unpaid[0]["monthly_payment"], unpaid[1]["balance"])
                        unpaid[1]["balance"] -= extra
                        total_payment += extra

                    hist.append(round(sum(l["balance"] for l in loans), 2))
                    months += 1

                result["snowball"] = {
                    "months_to_payoff": months,
                    "data_json"       : json.dumps(hist),
                    "total_paid"      : round(total_payment, 2),
                    "total_interest"  : round(total_interest, 2),
                }

                DebtCalculation.objects.create(
                    user              = request.user,
                    months_to_freedom = months,
                    total_balance     = total_balance,
                    total_payment     = total_payment,
                    total_interest    = total_interest,
                    strategy          = "snowball",
                    extra_payment     = 0,
                    loan_summary      = ", ".join(f"{l['name']} (${l['initial_balance']:.0f})" for l in loans),
                    loan_data         = loans,
                )

            # ───────────────────── 6) 50/30/20 BUDGET  ────────────────────
            mortgage_pmt  = result["mortgage"]["monthly_payment"]
            debt_pmt      = sum(l["monthly_payment"] for l in loans) if loans else 0
            retirement_pmt= round(annual_income*contrib_pct/12, 2)
            savings_pmt   = sc
            leftover      = max(0, monthly_net - (mortgage_pmt+debt_pmt+retirement_pmt+savings_pmt))

            result["budget"] = {
                "monthly_income": monthly_net,
                "expenses": {
                    "Mortgage"  : mortgage_pmt,
                    "Debt"      : debt_pmt,
                    "Retirement": retirement_pmt,
                    "Savings"   : savings_pmt,
                },
                "leftover"           : leftover,
                "needs"              : round(leftover*0.50, 2),
                "wants"              : round(leftover*0.30, 2),
                "additional_savings" : round(leftover*0.20, 2),
            }

            BudgetCalculation.objects.create(
                user            = request.user,
                monthly_income  = monthly_net,
                total_expenses  = mortgage_pmt+debt_pmt+retirement_pmt+savings_pmt,
                savings_goal    = savings_pmt + round(leftover*0.20, 2),
            )

        else:
            error = "Please fix the highlighted errors below."

    else:  # GET
        form          = MergeForm()
        loan_formset  = LoanFormSet(prefix="loans")

    return render(
        request,
        "main/merge_calculator.html",
        {"form": form, "loan_formset": loan_formset, "result": result, "error": error},
    )