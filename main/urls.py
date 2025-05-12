from django.urls import path
from .views import landing, login_view, about, register, dashboard_view
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views
from .views import snowball_calculator


urlpatterns = [
    path('', landing, name='landing'),
    path('HomePage', landing, name='landing'),
    path('about/', about, name='about'),
    path('login/', login_view, name='login'),
    path('register/', register, name='register'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),
    #path('accounts/login/', auth_views.LoginView.as_view(template_name='main/login.html'), name='login'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='main/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='main/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='main/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='main/password_reset_complete.html'), name='password_reset_complete'),
    path('debt-calculator/', snowball_calculator, name='debt_calculator'),

]

