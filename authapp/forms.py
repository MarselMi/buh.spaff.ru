from django.contrib.auth.forms import AuthenticationForm
from django import forms


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

