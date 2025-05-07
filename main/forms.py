from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm



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