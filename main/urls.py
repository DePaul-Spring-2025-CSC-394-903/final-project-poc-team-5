from django.urls import path
from main.views import (
    landing,
    login_view,
    about,
    register,
    dashboard_view,
    snowball_calculator,
    calculator_401k,
    budgeting_tool,
    savings_calculator,
    SafeLogoutView,
    snowball_result_view,
)
from main import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', landing, name='landing'),
    path('HomePage/', landing, name='home_redirect'),

    path('about/', about, name='about'),
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', SafeLogoutView.as_view(next_page='/login/'), name='logout'),

    # Password reset flow
    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(template_name='main/password_reset_form.html'),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='main/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='main/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='main/password_reset_complete.html'),
        name='password_reset_complete'
    ),

    # Debt / Snowball
    path('debt-calculator/', snowball_calculator, name='debt_calculator'),
    path('snowball-result/', snowball_result_view, name='snowball_result'),
    path('snowball-history/', views.snowball_history, name='snowball_history'),
    path('delete-calculation/<int:pk>/', views.delete_calculation, name='delete_calculation'),

    # 401(k)
    path('401k-calculator/', calculator_401k, name='calculator_401k'),
    path('401k-history/', views.retirement_history, name='retirement_history'),
    path('401k-result/', views.retirement_result_view, name='retirement_result'),
    path('401k-history/delete/<int:pk>/', views.delete_retirement_entry, name='delete_401k'),
    path('401k-history/edit/<int:pk>/', views.edit_retirement_entry, name='edit_401k'),

    # Budgeting
    path('budgeting-tool/', budgeting_tool, name='budgeting_tool'),
    path('budget/reset-income/', views.reset_income, name='reset_income'),
    path('budget/history/', views.budget_history, name='budget_history'),
    path('budget/edit/<int:pk>/', views.edit_budget_entry, name='edit_budget_entry'),
    path('budget/delete/<int:pk>/', views.delete_budget_entry, name='delete_budget_entry'),
    path('budget/latest/', views.latest_budget_result, name='latest_budget_result'),

    # Savings
    path('savings-calculator/', savings_calculator, name='savings_calculator'),
    path('savings/history/', views.savings_history, name='savings_history'),
    path('savings/edit/<int:pk>/', views.edit_savings_entry, name='edit_savings_entry'),
    path('savings/delete/<int:pk>/', views.delete_savings_entry, name='delete_savings_entry'),
    path('savings/latest/', views.latest_savings_result, name='latest_savings_result'),
    path('savings/result/', views.latest_savings_result, name='latest_savings_result'),  # alias

    # Take-Home
    path('take-home-calculator/', views.take_home_calculator, name='take_home_calculator'),
    path('take-home/history/', views.take_home_history, name='take_home_history'),
    path('takehome/edit/<int:pk>/', views.edit_take_home_entry, name='edit_take_home_entry'),
    path('takehome/delete/<int:pk>/', views.delete_take_home_entry, name='delete_take_home_entry'),
    path('take-home/latest/', views.latest_take_home_result, name='latest_take_home_result'),

    # Mortgage
    path('mortgage/', views.mortgage_calculator, name='mortgage_calculator'),
    path('mortgage/history/', views.mortgage_history, name='mortgage_history'),
    path('mortgage/edit/<int:pk>/', views.edit_mortgage_entry, name='edit_mortgage_entry'),
    path('mortgage/delete/<int:pk>/', views.delete_mortgage_entry, name='delete_mortgage_entry'),
    path('mortgage/latest/', views.latest_mortgage_result, name='latest_mortgage_result'),
    path('savings/latest/', views.latest_savings_result, name='latest_savings_result'),
    path('takehome/latest/', views.latest_take_home_result, name='latest_take_home_result'),
    path('debt-breakdown/', views.snowball_monthly_breakdown, name='snowball_monthly_breakdown'),

    # Calculator Info
    path("calculator-info/", views.calculator_info_view, name="calculator_info"),

    # Merge all calculators
    path("merge/", views.merge_calculator, name="merge_calculator"),


    path("summary/", views.financial_summary, name="financial_summary"),

]
