from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django import forms
from authapp.models import CustomUser


class CustomUserCreationForm(UserCreationForm):

    class Meta:
        model = CustomUser
        fields = ('username',)


class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ('username',)


class LoginUserForm(AuthenticationForm):

    username = forms.CharField(label='Логин', widget=forms.TextInput(
                attrs={
                    'class': 'form-control mb-4',
                    'placeholder': 'Введите свой Email'
                }))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(
                attrs={
                    'class': 'form-control mb-4',
                    'placeholder': 'Введите пароль'
                }))

