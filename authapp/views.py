from django.http import JsonResponse
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from authapp.forms import LoginUserForm
from django.contrib import messages
from mainapp.data_library import *
from mainapp.models import CustomUser, BalanceHolder
from django.contrib.auth.hashers import make_password


def users_view(request):

    all_users = get_users_information()

    for us in all_users:
        if us.get('balanceholder_id'):
            holders = us.get('balanceholder_id').split(',')
            new_list_bal = []
            for i in holders:
                bal_hole = BalanceHolder.objects.filter(organization_holder=i)
                if bal_hole[0].hidden_status == 1:
                    if request.user in bal_hole[0].available_superuser.all():
                        new_list_bal.append(bal_hole[0].organization_holder)
                else:
                    new_list_bal.append(bal_hole[0].organization_holder)
            us['balanceholder_id'] = new_list_bal

    data = {'title': 'Пользователи', 'users': all_users}

    return render(request, 'authapp/users.html', data)


def create_user_view(request):

    balalance_holders = BalanceHolder.objects.filter(deleted=False)

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

        new_user = CustomUser

        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        holders_id = []
        all_holders = BalanceHolder.objects.all()
        for hol in all_holders:
            if str(hol.pk) in request.POST:
                holders_id.append(hol.pk)

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

        if is_superuser:
            new_user.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                is_superuser=is_superuser,
                password=password1
            )
        else:
            obj = new_user.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                password=password1
            )
            for i in holders_id:
                bal_holder = BalanceHolder.objects.filter(pk=i)
                obj.available_holders.add(i)
                bal_holder[0].available_superuser.add(obj.id)

        return redirect('users')

    data = {'title': 'Создание пользователя',  'inside': {'page_url': 'users', 'page_title': 'Пользователи'},
            'balance_holders': balalance_holders}

    return render(request, 'authapp/create_user.html', data)


def edit_user_view(request, pk):

    user_edit = CustomUser.objects.filter(pk=pk)
    bal_hol = get_holders_user(pk)
    bal_hol_id_list = []
    for holder_id in bal_hol:
        bal_hol_id_list.append(holder_id['balanceholder_id'])

    balance_holders = get_allow_balance_holders(request.user.id, simple_user=False)

    if request.method == 'POST':

        if request.POST.get('type') == 'check_username':
            username = request.POST.get('username')
            if CustomUser.objects.filter(username=username).exists():
                if username == user_edit[0].username:
                    return JsonResponse({'message': True})
                else:
                    return JsonResponse({'message': False})
            else:
                return JsonResponse({'message': True})

        if request.POST.get('type') == 'check_password':
            password = request.POST.get('password')
            if user_edit[0].check_password(password):
                return JsonResponse({'message': True})
            else:
                return JsonResponse({'message': False})

        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        holders_id = []
        all_holders = BalanceHolder.objects.all()
        for hol in all_holders:
            bal_holder = BalanceHolder.objects.filter(pk=hol.pk)
            if str(hol.pk) in request.POST:
                holders_id.append(hol.pk)
                bal_holder[0].available_superuser.add(pk)
            else:
                bal_holder[0].available_superuser.remove(pk)

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
            user_edit.update(
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                is_superuser=is_superuser,
                password=make_password(password1)
            )
        else:
            user_edit.update(
                username=username,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff,
                is_superuser=is_superuser
            )

        if user_edit[0].is_superuser:
            pass
        else:
            user_edit[0].available_holders.set(holders_id)
            user_edit[0].save()
        return redirect('users')

    data = {'title': 'Редактирование пользователя', 'inside': {'page_url': 'users', 'page_title': 'Пользователи'},
            'user_edit': user_edit[0], 'balance_holders': balance_holders, 'bal_hol': bal_hol_id_list}

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

