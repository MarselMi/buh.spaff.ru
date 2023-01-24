from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView
from authapp.forms import LoginUserForm  # CreateUserForm
from django.contrib import messages


class CustomLoginView(LoginView):
    template_name = 'mainapp/sign-in.html'
    form_class = LoginUserForm


def custom_login(request):
    if request.method == "POST":
        form = LoginUserForm(request.POST)
        if form.is_valid():
            return redirect(request, 'mainapp/main-page.html')
        else:
            messages.error(request, 'Неверен логин или пароль')
            messages.error(request, form.errors)
    else:
        form = LoginUserForm()
    return render(request, 'mainapp/sign-in.html', {'form': form})


class CustomLogoutView(LogoutView):
    pass

