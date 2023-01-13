from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView
from authapp.forms import LoginUserForm  # CreateUserForm


class CustomLoginView(LoginView):
    template_name = 'mainapp/sign-in.html'
    form_class = LoginUserForm


class CustomLogoutView(LogoutView):
    pass

