from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    landing, login_view, about, register, dashboard_view,
    snowball_calculator, calculator_401k, SafeLogoutView
)

urlpatterns = [
    path('', landing, name='landing'),
    path('HomePage/', landing, name='home_redirect'),

    path('about/', about, name='about'),
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', SafeLogoutView.as_view(next_page='/login/'), name='logout'),

    # Auth: password reset flow
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='main/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='main/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='main/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='main/password_reset_complete.html'), name='password_reset_complete'),

    # Tools
    path('debt-calculator/', snowball_calculator, name='debt_calculator'),
    path('401k-calculator/', calculator_401k, name='calculator_401k'),
    
]