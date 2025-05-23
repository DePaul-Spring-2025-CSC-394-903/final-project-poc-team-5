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
from .utils import calcGains
from django.contrib.auth.views import LogoutView
from django.http import HttpResponseNotAllowed
from .models import RetirementCalculation
from datetime import datetime
from django.http import HttpResponseRedirect
from django.urls import reverse



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


class LoanForm(forms.Form):
    name = forms.CharField(label="Loan Name", required=True)
    balance = forms.DecimalField(label="Balance ($)", min_value=0)
    monthly_payment = forms.DecimalField(label="Monthly Payment ($)", min_value=0)
    interest_rate = forms.DecimalField(label="Annual Interest Rate (%)", min_value=0)


LoanFormSet = formset_factory(LoanForm, extra=1, can_delete=True)


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
    })


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

    return render(request, 'main/dashboard.html', {
        'history': history,
        'has_result': has_result,
        'has_401k_result': has_401k_result,
    })



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

            # Load selected debt (snowball) entry
            snowball_monthly = 0
            if selected_debt_id:
                debt_entry = DebtCalculation.objects.filter(user=user, pk=selected_debt_id).first()
                if debt_entry:
                    snowball_monthly = float(debt_entry.total_payment) / float(debt_entry.months_to_freedom)

            # Load selected 401(k) retirement entry
            retirement_monthly = 0
            if selected_401k_id:
                retirement_entry = RetirementCalculation.objects.filter(user=user, pk=selected_401k_id).first()
                if retirement_entry:
                    retirement_monthly = float(retirement_entry.salary) * (float(retirement_entry.contribution) / 100) / 12

            # Fixed ratios for categories (should sum to 1.0)
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

            # Calculate base category allocations
            base_allocations = [round(remaining_income * ratios[cat], 2) for cat in ratios]

            savings = round(retirement_monthly, 2)
            debt = round(snowball_monthly, 2)

            final_allocations = base_allocations[:5] + [savings, debt, base_allocations[5]]

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



@require_POST
@login_required
def reset_income(request):
    request.session.pop("fixed_income", None)
    return redirect('budgeting_tool')
