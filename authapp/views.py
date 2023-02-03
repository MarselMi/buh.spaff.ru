from django.http import JsonResponse
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from authapp.forms import LoginUserForm
from django.contrib import messages
from mainapp.models import CustomUser, BalanceHolder
from django.contrib.auth.hashers import make_password


def users_view(request):

    all_users = CustomUser.objects.all()

    data = {'title': 'Пользователи',
            'users': all_users}

    return render(request, 'authapp/users.html', data)


def create_user_view(request):

    if request.method == 'POST':

        if request.POST.get('type') == 'check_username':
            username = request.POST.get('username')
            if CustomUser.objects.filter(username=username).exists():
                return JsonResponse(
                    {'message': False}
                )
            else:
                return JsonResponse(
                    {'message': True}
                )

        user = CustomUser

        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        is_staff = request.POST.get('is_staff')
        if is_staff:
            is_staff = True
        else:
            is_staff = False

        is_superuser = request.POST.get('is_superuser')
        if is_superuser:
            is_superuser = True
        else:
            is_superuser = False

        password1 = request.POST.get('password1')

        user.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_staff=is_staff,
            is_superuser=is_superuser,
            password=password1
        )
        return redirect('users')

    data = {'title': 'Создание пользователя',  'inside': {'page_url': 'users', 'page_title': 'Пользователи'},
            }

    return render(request, 'authapp/create_user.html', data)


def edit_user_view(request, pk):

    user = CustomUser.objects.filter(pk=pk)

    balance_holders = BalanceHolder.objects.all()

    if request.method == 'POST':

        if request.POST.get('type') == 'check_username':
            username = request.POST.get('username')
            if CustomUser.objects.filter(username=username).exists():
                if username == user[0].username:
                    return JsonResponse(
                        {'message': True}
                    )
                else:
                    return JsonResponse(
                        {'message': False}
                    )
            else:
                return JsonResponse(
                    {'message': True}
                )

        if request.POST.get('type') == 'check_password':
            password = request.POST.get('password')
            if user[0].check_password(password):
                return JsonResponse(
                    {'message': True}
                )
            else:
                return JsonResponse(
                    {'message': False}
                )

        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        is_staff = request.POST.get('is_staff')
        if is_staff:
            is_staff = True
        else:
            is_staff = False

        is_superuser = request.POST.get('is_superuser')
        if is_superuser:
            is_superuser = True
        else:
            is_superuser = False

        password1 = request.POST.get('password1')
        if password1:
            user.update(
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                is_superuser=is_superuser,
                password=make_password(password1)
            )
        else:
            user.update(
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                is_superuser=is_superuser
            )

        return redirect('users')

    data = {'title': 'Редактирование пользователя', 'inside': {'page_url': 'users', 'page_title': 'Пользователи'},
            'user': user[0], 'balance_holders': balance_holders}

    return render(request, 'authapp/edit_user.html', data)


class CustomLoginView(LoginView):
    template_name = 'authapp/sign-in.html'
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
    return render(request, 'authapp/sign-in.html', {'form': form})


class CustomLogoutView(LogoutView):
    pass

