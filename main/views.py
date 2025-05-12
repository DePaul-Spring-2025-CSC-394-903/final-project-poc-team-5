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
from decimal import Decimal


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

class SnowballForm(forms.Form):
    balance = forms.DecimalField(
        label="Credit Card Debt",
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    monthly_payment = forms.DecimalField(
        label="Current Monthly Payment",
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    additional_payment = forms.DecimalField(
        label="Additional Payment",
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={
            'type': 'range', 'min': '0', 'max': '1000', 'step': '5',
            'class': 'form-range',
            'id': 'id_additional_payment'
        })
    )


@login_required
def snowball_calculator(request):
    result = None
    if request.method == 'POST':
        form = SnowballForm(request.POST)
        if form.is_valid():
            balance = form.cleaned_data['balance']
            monthly = form.cleaned_data['monthly_payment']
            extra = form.cleaned_data['additional_payment']
            payment = monthly + extra
            current = balance
            months = 0
            chart_data = []

            while current > 0:
                interest = current * Decimal("0.02")
                current += interest - payment
                current = max(current, 0)
                chart_data.append(round(current, 2))
                months += 1
                if months > 600:
                    break

            result = {
                'months': months,
                'final_payment': float(payment),
                'data_json': json.dumps([float(x) for x in chart_data])  # ✅ convert Decimals to float
            }

            DebtCalculation.objects.create(
                user=request.user,
                balance=balance,
                monthly_payment=monthly,
                additional_payment=extra,
                months_to_freedom=months
            )
    else:
        form = SnowballForm()

    return render(request, 'main/snowball_calculator.html', {'form': form, 'result': result})

@login_required
def dashboard_view(request):
    history = DebtCalculation.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'main/dashboard.html', {'history': history})