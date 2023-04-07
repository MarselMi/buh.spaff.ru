import json
import decimal
from hashlib import md5
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from datetime import datetime as dt
from mainapp.data_library import *
from mainapp.forms import (
    TransactionForm, BalanceHolderForm, TransactionUpdateForm
)
from mainapp.models import (
    CustomUser, Transaction, BalanceHolder, PayType,
    AdditionalDataTransaction, TransactionLog, SubPayType
)


def main_page_view(request):
    holders = []
    comming_sum = ''
    expenditure_sum = ''
    all_coming = 0
    all_expenditure = 0
    if request.user.is_superuser:
        holders = BalanceHolder.objects.filter(deleted=False)
        comming_sum = get_all_coming_transactions_sum(request.user.id, simpleuser=False)
        expenditure_sum = get_all_expenditure_transactions_sum(request.user.id, simpleuser=False)
    else:
        holders = get_allow_balance_holders(request.user.id)
        comming_sum = get_all_coming_transactions_sum(request.user.id, simpleuser=True)
        expenditure_sum = get_all_expenditure_transactions_sum(request.user.id, simpleuser=True)

    type_payments = PayType.objects.all()

    try:
        for k in comming_sum:
            all_coming += k.get('coming')
    except:
        pass

    try:
        for k in expenditure_sum:
            all_expenditure += k.get('expenditure')
    except:
        pass

    if request.method == 'POST':

        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                pay_type_element = PayType.objects.filter(pay_type=pay_type)[0].subtypes_of_the_type.all()
                sub_type_pay = []
                for i in pay_type_element:
                    sub_type_pay.append(i.sub_type)
                return JsonResponse({'message': sub_type_pay})
            else:
                return JsonResponse({'message': False})

        if request.POST.get('type') == 'create_transaction':

            holder = BalanceHolder.objects.filter(organization_holder=request.POST.get('holder_post'))[0]

            transaction_name = request.POST.get('transaction_name_post')
            transaction_date = dt.strptime(request.POST.get('transaction_date_post'), '%d.%m.%Y').date()
            payment_type = PayType.objects.filter(pay_type=request.POST.get('payment_type_post'))[0]
            sub_type = None
            if request.POST.get('sub_type'):
                sub_type = SubPayType.objects.filter(sub_type=request.POST.get('sub_type'))[0]

            commission = 0
            if request.POST.get('commission_post'):
                commission = decimal.Decimal(request.POST.get('commission_post').replace(',', '.').replace(' ', ''))
            transaction_sum = decimal.Decimal(request.POST.get('transaction_sum_post').replace(',', '.').replace(' ', ''))
            amount = transaction_sum + commission

            transaction_type = request.POST.get('transaction_type_post')

            if transaction_type == 'Приход':
                transaction_type = 'COMING'
            else:
                transaction_type = 'EXPENDITURE'

            author_id = request.user.id

            create_transaction = {
                'sub_type_pay': sub_type,
                'type_transaction': transaction_type,
                'transaction_date': transaction_date,
                'name': transaction_name,
                'balance_holder': holder,
                'commission': commission,
                'transaction_sum': transaction_sum,
                'amount': amount,
                'type_payment': payment_type,
                'author_id': author_id
            }

            transaction = Transaction

            transaction.objects.create(**create_transaction)

            balance_holder_response = BalanceHolder.objects.filter(organization_holder=holder)
            old_balance_balance_holder = balance_holder_response[0].holder_balance
            if transaction_type == 'COMING':
                old_balance_balance_holder += amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
            else:
                old_balance_balance_holder -= amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)

            return HttpResponse(json.dumps({"Status": "OK"}))

        if request.POST.get('type') == 'holder':
            holder_id = request.POST.get('id')
            holder_transaction_coming = get_all_coming_transactions_sum(request.user.id, holder=holder_id)
            holder_transaction_expenditure = get_all_expenditure_transactions_sum(request.user.id, holder=holder_id)

            holder_label_expenditure = []
            holder_profit_expenditure = []
            holder_label_coming = []
            holder_profit_coming = []

            for i in holder_transaction_coming:
                holder_label_coming.append(i['type'])
                holder_profit_coming.append(float(i['coming']))

            for i in holder_transaction_expenditure:
                holder_label_expenditure.append(i['type'])
                holder_profit_expenditure.append(float(i['expenditure']))

            data = {
                'holder_label_expenditure': holder_label_expenditure,
                'holder_profit_expenditure': holder_profit_expenditure,
                'holder_label_coming': holder_label_coming,
                'holder_profit_coming': holder_profit_coming
            }

            return HttpResponse(json.dumps(data))

    # color_list = ['primary', 'secondary', 'success', 'info', 'light', 'danger', 'warning', 'dark',
    #               'primary', 'secondary', 'success', 'info', 'light', 'danger', 'warning', 'dark',
    #               'primary', 'secondary', 'success', 'info', 'light', 'danger', 'warning', 'dark',
    #               'primary', 'secondary', 'success', 'info', 'light', 'danger', 'warning', 'dark']

    label_coming = []
    profit_coming = []
    for i in comming_sum:
        label_coming.append(i['type'])
        profit_coming.append(float(i['coming']))

    label_expenditure = []
    profit_expenditure = []
    for i in expenditure_sum:
        label_expenditure.append(i['type'])
        profit_expenditure.append(float(i['expenditure']))

    data = {'title': 'Главная страница', 'holders': holders,
            'type_payments': type_payments, 'comming_sum': comming_sum, 'expenditure_sum': expenditure_sum,
            'label_coming': label_coming, 'profit_coming': profit_coming, 'profit_expenditure': profit_expenditure,
            'label_expenditure': label_expenditure, 'all_coming': all_coming, 'all_expenditure': all_expenditure
            }

    return render(request, 'mainapp/main-page.html', data)


def transaction_view(request):
    balance_holders = []
    transactions = []
    authors = CustomUser.objects.all()
    type_payments = PayType.objects.all()
    sub_type = SubPayType.objects.all()
    dict_for_sql_filter = dict()
    get_param_filter = dict(request.GET)

    collapsed = request.session.get('transaction_collapse')
    if collapsed is None:
        request.session['transaction_collapse'] = 2

    ''' Заполенние словаря для SQL-запроса '''
    for element in get_param_filter:
        if get_param_filter.get(element) != [''] and element != 'collapse' and element != 'csrfmiddlewaretoken':
            dict_for_sql_filter.setdefault(element, get_param_filter[element][0])

    '''Заменяю данные для отработки SQL запроса '''
    if dict_for_sql_filter.get('type_payment_id'):
        dict_for_sql_filter['type_payment_id'] = type_payments.filter(pay_type=dict_for_sql_filter.get('type_payment_id')).values('id')[0].get('id')

    if dict_for_sql_filter.get('sub_type_pay_id'):
        dict_for_sql_filter['sub_type_pay_id'] = sub_type.filter(sub_type=dict_for_sql_filter.get('sub_type_pay_id')).values('id')[0].get('id')

    if dict_for_sql_filter.get('author_id'):
        dict_for_sql_filter['author_id'] = authors.filter(username=dict_for_sql_filter.get('author_id')).values('id')[0].get('id')

    if dict_for_sql_filter.get('balance_holder_id'):
        dict_for_sql_filter['balance_holder_id'] = BalanceHolder.objects.filter(organization_holder=dict_for_sql_filter.get('balance_holder_id')).values('id')[0].get('id')

    if dict_for_sql_filter.get('amount_start'):
        dict_for_sql_filter['amount_start'] = dict_for_sql_filter.get('amount_start').replace(' ', '').replace(',', '.')

    if dict_for_sql_filter.get('amount_end'):
        dict_for_sql_filter['amount_end'] = dict_for_sql_filter.get('amount_end').replace(' ', '').replace(',', '.')

    if dict_for_sql_filter.get('start'):
        dict_for_sql_filter['start'] = dt.strptime(dict_for_sql_filter.get('start'), '%d.%m.%Y').strftime('%Y-%m-%d')

    if dict_for_sql_filter.get('end'):
        dict_for_sql_filter['end'] = dt.strptime(dict_for_sql_filter.get('end'), '%d.%m.%Y').strftime('%Y-%m-%d')

    if request.user.is_superuser:
        balance_holders = get_allow_balance_holder_transactions(request.user.id, superuser_role=True)
        transactions = get_allow_transaction_filter(request.user.id, filter_data=dict_for_sql_filter)
    else:
        balance_holders = get_allow_balance_holder_transactions(request.user.id)
        transactions = get_allow_transaction_filter(request.user.id, filter_data=dict_for_sql_filter, author_res=True)

    if request.GET.get('collapse'):
        collapsed = request.session.get('transaction_collapse')
        if collapsed == 2:
            request.session['transaction_collapse'] = 1
        else:
            request.session['transaction_collapse'] = 2

    data = {'title': 'Транзакции', 'balance_holders': balance_holders, 'type_payments': type_payments,
            'transactions': transactions, 'authors': authors, 'get_param_filter': get_param_filter,
            'collapsed': collapsed, 'sub_type': sub_type}

    return render(request, 'mainapp/transactions.html', data)


def create_transaction_view(request):

    transaction = Transaction
    form = TransactionForm
    type_payments = PayType.objects.all()
    balance_holders = []
    if request.user.is_superuser:
        balance_holders = BalanceHolder.objects.all()
    else:
        for holder in get_allow_balance_holder_transactions(request.user.id):
            balance_holders.append(holder['organization_holder'])

    if request.method == 'POST':
        if request.POST.get('type') == 'check_holder':
            organization_holder = request.POST.get('balance_holder')
            if BalanceHolder.objects.filter(organization_holder=organization_holder).exists():
                return JsonResponse({'message': True})
            else:
                return JsonResponse({'message': False})

        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                pay_type_element = PayType.objects.filter(pay_type=pay_type)[0].subtypes_of_the_type.all()
                sub_type_pay = []
                for i in pay_type_element:
                    sub_type_pay.append(i.sub_type)
                return JsonResponse({'message': sub_type_pay})
            else:
                return JsonResponse({'message': False})

        holder_response = request.POST.get('balance_holder')
        balance_holder_response = BalanceHolder.objects.filter(organization_holder=holder_response)
        sub_type = None
        if request.POST.get('sub_type'):
            sub_type = SubPayType.objects.filter(sub_type=request.POST.get('sub_type'))[0]
        name = request.POST.get('transaction_name')

        status = request.POST.get('transaction_status')
        if status == 'В процессе':
            status = 'INPROCESS'
        elif status == 'Отклонен':
            status = 'REJECT'
        else:
            status = 'SUCCESSFULLY'

        transaction_date = dt.strptime(request.POST.get('transaction_date'), '%d.%m.%Y').date()

        type_payment = PayType.objects.filter(pay_type=request.POST.get('type_payment'))[0]

        commission = 0
        if request.POST.get('commission_post'):
            commission = decimal.Decimal(request.POST.get('commission_post').replace(',', '.').replace(' ', ''))
        transaction_sum = decimal.Decimal(request.POST.get('transaction_sum_post').replace(',', '.').replace(' ', ''))
        amount = transaction_sum + commission

        type_transaction = request.POST.get('type_transaction')
        if type_transaction == 'Приход':
            type_transaction = 'COMING'
        else:
            type_transaction = 'EXPENDITURE'

        '''Логика для загрузки ЧЕКов'''
        image = request.FILES.get('check_img')
        if image:
            check_img = f"img/{str(image).replace(' ', '_')}"
            root = f'{settings.MEDIA_ROOT}/{str(check_img)}'
            with open(root, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)
            image = check_img

        description = request.POST.get('description')
        tags = request.POST.get('tags')

        author_id = request.user.id

        new_data = {
            'transaction_date': transaction_date, 'type_transaction': type_transaction,
            'name': name, 'description': description, 'balance_holder': balance_holder_response[0],
            'amount': amount, 'type_payment': type_payment, 'status': status, 'tags': tags,
            'check_img': image, 'author_id': author_id, 'commission': commission, 'transaction_sum': transaction_sum,
            'sub_type_pay': sub_type
        }

        transaction.objects.create(**new_data)

        old_balance_balance_holder = balance_holder_response[0].holder_balance
        if status == 'SUCCESSFULLY':
            if type_transaction == 'COMING':
                old_balance_balance_holder += amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
            else:
                old_balance_balance_holder -= amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
        else:
            pass
        return redirect('transactions')

    data = {'title': 'Создание транзакции', 'inside': {'page_url': 'transactions', 'page_title': 'Транзакции'},
            'form': form, 'type_payments': type_payments, 'balance_holders': balance_holders}

    return render(request, 'mainapp/transaction_create.html', data)


def create_transaction_holder_view(request, pk):

    transaction = Transaction
    form = TransactionForm
    type_payments = PayType.objects.all()
    balance_holders_pk = BalanceHolder.objects.filter(pk=pk)
    balance_holders = BalanceHolder.objects.all()

    if request.method == 'POST':
        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                pay_type_element = PayType.objects.filter(pay_type=pay_type)[0].subtypes_of_the_type.all()
                sub_type_pay = []
                for i in pay_type_element:
                    sub_type_pay.append(i.sub_type)
                return JsonResponse({'message': sub_type_pay})
            else:
                return JsonResponse({'message': False})

        holder_response = request.POST.get('balance_holder')

        balance_holder_response = BalanceHolder.objects.filter(organization_holder=holder_response)

        name = request.POST.get('transaction_name')

        status = request.POST.get('transaction_status')
        if status == 'В процессе':
            status = 'INPROCESS'
        elif status == 'Отклонен':
            status = 'REJECT'
        else:
            status = 'SUCCESSFULLY'

        transaction_date = dt.strptime(request.POST.get('transaction_date'), '%d.%m.%Y').date()

        type_payment = PayType.objects.filter(pay_type=request.POST.get('type_payment'))[0]

        sub_type = None
        if request.POST.get('sub_type'):
            sub_type = SubPayType.objects.filter(sub_type=request.POST.get('sub_type'))[0]

        commission = 0
        if request.POST.get('commission_post'):
            commission = decimal.Decimal(request.POST.get('commission_post').replace(',', '.').replace(' ', ''))
        transaction_sum = decimal.Decimal(request.POST.get('transaction_sum_post').replace(',', '.').replace(' ', ''))
        amount = transaction_sum + commission

        type_transaction = request.POST.get('type_transaction')
        if type_transaction == 'Приход':
            type_transaction = 'COMING'
        else:
            type_transaction = 'EXPENDITURE'

        '''Логика для загрузки ЧЕКов'''
        image = request.FILES.get('check_img')
        if image:
            check_img = f"img/{str(image).replace(' ', '_')}"
            root = f'{settings.MEDIA_ROOT}/{str(check_img)}'
            with open(root, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)
            image = check_img

        description = request.POST.get('description')
        tags = request.POST.get('tags')

        author_id = request.user.id

        new_data = {
            'transaction_date': transaction_date, 'type_transaction': type_transaction,
            'name': name, 'description': description, 'balance_holder': balance_holder_response[0],
            'amount': amount, 'type_payment': type_payment, 'status': status, 'tags': tags,
            'check_img': image, 'author_id': author_id, 'commission': commission, 'transaction_sum': transaction_sum,
            'sub_type_pay': sub_type
        }

        transaction.objects.create(**new_data)

        old_balance_balance_holder = balance_holder_response[0].holder_balance
        if status == 'SUCCESSFULLY':
            if type_transaction == 'COMING':
                old_balance_balance_holder += amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
            else:
                old_balance_balance_holder -= amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
        else:
            pass
        return redirect('transactions')

    data = {'title': 'Создание транзакции', 'inside': {'page_url': 'transactions', 'page_title': 'Транзакции'},
            'form': form, 'type_payments': type_payments, 'balance_holders': balance_holders,
            'holder_pk': balance_holders_pk[0]}

    return render(request, 'mainapp/transaction_holder_create.html', data)


def transaction_update_view(request, pk):

    transaction = Transaction.objects.filter(pk=pk)
    form_class = TransactionUpdateForm(request.POST, request.FILES)
    type_payments = PayType.objects.all()
    sub_type_of_type = type_payments.filter(pay_type=transaction[0].type_payment)[0].subtypes_of_the_type.all()

    old_transaction = transaction.values(
        'status', 'transaction_date', 'amount', 'description', 'type_payment', 'check_img', 'sub_type_pay'
    )

    if request.method == 'POST':
        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                pay_type_element = PayType.objects.filter(pay_type=pay_type)[0].subtypes_of_the_type.all()
                sub_type_pay = []
                for i in pay_type_element:
                    sub_type_pay.append(i.sub_type)
                return JsonResponse({'message': sub_type_pay})
            else:
                return JsonResponse({'message': False})

        status = request.POST.get('transaction_status')

        '''Данные через форму'''
        transaction_date = dt.strptime(request.POST.get('transaction_date'), '%d.%m.%Y').date()
        amount = decimal.Decimal(request.POST.get('amount').replace(',', '.').replace(' ', ''))
        type_payment = PayType.objects.filter(pay_type=request.POST.get('type_payment'))[0].pk
        sub_type = None
        if request.POST.get('sub_type'):
            sub_type = SubPayType.objects.filter(sub_type=request.POST.get('sub_type'))[0].pk

        '''Логика для загрузки ЧЕКов'''
        check_img = ''
        image = request.FILES.get('check_img')
        if image:
            check_img = f"img/{str(image).replace(' ', '_')}"
            root = f'{settings.MEDIA_ROOT}/{str(check_img)}'
            with open(root, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)
        if check_img == '' or check_img is None:
            check_img = transaction[0].check_img

        description = None
        if request.POST.get('description'):
            description = request.POST.get('description')

        tags = None
        if request.POST.get('tags'):
            tags = request.POST.get('tags')

        '''Словарь новых данных по форме'''
        new_transaction_data = {'status': status, 'transaction_date': transaction_date,
                                'amount': amount, 'type_payment': type_payment, 'check_img': check_img,
                                'tags': tags, 'description': description, 'sub_type_pay': sub_type}

        changes = {'transaction_id': pk, 'author_references': request.user}

        id_balance_holder = transaction[0].balance_holder.id
        balance_hodler = BalanceHolder.objects.filter(pk=id_balance_holder)
        old_balance_balance_holder = balance_hodler.values('holder_balance')[0]['holder_balance']

        for k in old_transaction[0]:
            check = new_transaction_data[k] == old_transaction[0][k]
            if not check:
                if k == 'transaction_date':
                    changes[k] = str(old_transaction[0][k].strftime('%d.%m.%Y'))+"/"+str(new_transaction_data[k].strftime('%d.%m.%Y'))
                changes[k] = str(old_transaction[0][k])+"/"+str(new_transaction_data[k])

        if changes.get('transaction_date'):
            date_split = changes['transaction_date'].split('/')
            date1 = (dt.strptime(date_split[0], '%Y-%m-%d').date()).strftime('%d.%m.%Y')
            date2 = (dt.strptime(date_split[1], '%Y-%m-%d').date()).strftime('%d.%m.%Y')
            dates = f'{date1}/{date2}'
            changes['transaction_date'] = dates

        if len(changes.values()) > 2:
            TransactionLog.objects.create(**changes)

        transaction.update(update_date=dt.now())

        if transaction[0].status != 'SUCCESSFULLY':
            if status == 'SUCCESSFULLY':
                if Transaction.objects.filter(pk=transaction[0].id).values('type_transaction')[0]['type_transaction'] == 'COMING':
                    old_balance_balance_holder += transaction[0].amount
                    balance_hodler.update(holder_balance=old_balance_balance_holder)
                else:
                    old_balance_balance_holder -= transaction[0].amount
                    balance_hodler.update(holder_balance=old_balance_balance_holder)
            else:
                pass

        if status == 'SUCCESSFULLY' and (amount != old_transaction[0]['amount']):
            if Transaction.objects.filter(pk=transaction[0].id).values('type_transaction')[0]['type_transaction'] == 'COMING':
                if amount > transaction[0].amount:
                    diff = amount - transaction[0].amount
                    old_balance_balance_holder += diff
                else:
                    diff = transaction[0].amount - amount
                    old_balance_balance_holder -= diff
                balance_hodler.update(holder_balance=old_balance_balance_holder)
            else:
                if amount > transaction[0].amount:
                    diff = amount - transaction[0].amount
                    old_balance_balance_holder -= diff
                else:
                    diff = transaction[0].amount - amount
                    old_balance_balance_holder += diff
                balance_hodler.update(holder_balance=old_balance_balance_holder)

        if (transaction[0].status == 'SUCCESSFULLY') and (status != 'SUCCESSFULLY'):
            if Transaction.objects.filter(pk=transaction[0].id).values('type_transaction')[0]['type_transaction'] == 'COMING':
                if amount > transaction[0].amount:
                    old_balance_balance_holder += amount
                else:
                    old_balance_balance_holder -= amount
                balance_hodler.update(holder_balance=old_balance_balance_holder)
            else:
                if amount > transaction[0].amount:
                    old_balance_balance_holder -= amount
                else:
                    old_balance_balance_holder += amount
                balance_hodler.update(holder_balance=old_balance_balance_holder)

        transaction.update(**new_transaction_data)

        return redirect('transactions')

    data = {'title': 'Изменение транзакции', 'inside': {'page_url': 'transactions', 'page_title': 'Транзакции'},
            'form': form_class, 'transaction': transaction[0], 'type_payments': type_payments,
            'sub_type_of_type': sub_type_of_type}

    return render(request, 'mainapp/transaction_edit.html', data)


def transactions_log_view(request):
    transactions_log = TransactionLog.objects.all()[::-1]
    data = {'title': 'Логи транзакций', 'transactions_log': transactions_log}
    return render(request, 'mainapp/transactions_log.html', data)


def balance_holders_views(request):
    if request.user.is_superuser:
        holders = get_allow_balance_holders(request.user.id, simple_user=False)
    else:
        holders = get_allow_balance_holders(request.user.id, simple_user=True)

    data = {'title': 'Балансодержатели', 'holders': holders}
    return render(request, 'mainapp/balance_holders.html', data)


def balance_holder_create_view(request):

    form_class = BalanceHolderForm

    if request.method == 'POST':

        if request.POST.get('type') == 'check_holder':
            organization_holder = request.POST.get('organization_holder')
            if BalanceHolder.objects.filter(organization_holder=organization_holder).exists():
                return JsonResponse({'message': False})
            else:
                return JsonResponse({'message': True})

        holder_type = request.POST.get('holder_type')
        account_type = request.POST.get('account_type')
        organization_holder = request.POST.get('organization_holder')
        payment_account = request.POST.get('payment_account').replace(' ', '')

        alias_holder = None
        if request.POST.get('alias_holder'):
            alias_holder = request.POST.get('alias_holder')

        holder_balance = 0
        if request.POST.get('holder_balance'):
            holder_balance = decimal.Decimal(request.POST.get('holder_balance').replace(',', '.').replace(' ', ''))

        new_balance_holder = BalanceHolder.objects.create(
            holder_type=holder_type,
            account_type=account_type,
            organization_holder=organization_holder,
            payment_account=payment_account,
            alias_holder=alias_holder,
            holder_balance=holder_balance
        )

        if request.user.is_superuser:
            pass
        else:
            request.user.available_holders.add(new_balance_holder.pk)

        return redirect('balance_holders')

    data = {'title': 'Создание балансодержателя', 'inside': {'page_url': 'holders', 'page_title': 'Балансодержатели'},
            'form': form_class}

    return render(request, 'mainapp/balance_holder_create.html', data)


def balance_holder_update_view(request, pk):

    update_balance_holder = BalanceHolder.objects.filter(pk=pk)

    if request.method == 'POST':

        if request.POST.get('type') == 'check_holder':
            organization_holder = request.POST.get('organization_holder')
            if BalanceHolder.objects.filter(organization_holder=organization_holder).exists():
                if BalanceHolder.objects.filter(organization_holder=organization_holder)[0] == BalanceHolder.objects.filter(pk=pk)[0]:
                    return JsonResponse(
                        {'message': True}
                    )
                return JsonResponse(
                    {'message': False}
                )
            else:
                return JsonResponse(
                    {'message': True}
                )
        holder_type = request.POST.get('holder_type')
        account_type = request.POST.get('account_type')
        organization_holder = request.POST.get('organization_holder')
        payment_account = request.POST.get('payment_account').replace(' ', '')

        alias_holder = None
        if request.POST.get('alias_holder'):
            alias_holder = request.POST.get('alias_holder')

        update_balance_holder.update(
            holder_type=holder_type,
            account_type=account_type,
            organization_holder=organization_holder,
            payment_account=payment_account,
            alias_holder=alias_holder,
        )

        return redirect('balance_holders')

    data = {'title': 'Редактирование балансодержателя', 'inside': {'page_url': 'holders', 'page_title': 'Балансодержатели'},
            'holder': update_balance_holder[0]}

    return render(request, 'mainapp/balance_holder_update.html', data)


def payment_type_view(request):
    pay_type = PayType.objects.all()
    sub_pay_types = SubPayType.objects.all()

    if request.method == 'POST':
        '''Проверка наличия подтипа платежа для избегания дублирования'''
        if request.POST.get('type') == 'check_sub_pay_type':
            sub_type = request.POST.get('sub_type_payment')
            if SubPayType.objects.filter(sub_type=sub_type).exists():
                return JsonResponse({'message': False})
            else:
                return JsonResponse({'message': True})
        '''создание подтипа платежа'''
        if request.POST.get('type') == 'new_sub_pay_type':
            sub_type = request.POST.get('sub_type_payment')
            sub_pay = SubPayType
            sub_pay.objects.create(sub_type=sub_type)
            return JsonResponse({'status': 'ok'})

        '''Проверка наличия типа платежа во избежания дублирования'''
        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                return JsonResponse({'message': False})
            else:
                return JsonResponse({'message': True})
        '''Создание типа платежа, с привязкой доп параметров при наличии'''
        if request.POST.get('type') == 'new_pay_type':
            pay_type = request.POST.get('type_payment')

            new_pay_type = PayType.objects.create(pay_type=pay_type)

            if request.POST.getlist('sub_type_payments[]'):
                sub_type_pay = request.POST.getlist('sub_type_payments[]')
                for i in sub_type_pay:
                    new_pay_type.subtypes_of_the_type.add(int(i))

            new_pay_type.save()
            return JsonResponse({'status': 'ok'})

        '''Выдача конкретного типа платежа для его редактирования'''
        if request.POST.get('type') == 'get_type_pay':
            sub_type_pay_el = PayType.objects.filter(pay_type=request.POST.get('type_pay'))[0].subtypes_of_the_type.all()
            sub_params = []
            for i in sub_type_pay_el:
                sub_params.append(i.id)

            return JsonResponse({'sub_params': sub_params})
        '''Редактирование типа платежа и добавление подтипов'''
        if request.POST.get('type') == 'add_sub_pay_type':
            pay_type = PayType.objects.filter(pay_type=request.POST.get('type_payment'))

            if request.POST.getlist('sub_type_payments[]'):
                sub_type_pay = request.POST.getlist('sub_type_payments[]')
                for i in sub_type_pay:
                    pay_type[0].subtypes_of_the_type.add(int(i))

            pay_type[0].save()
            return JsonResponse({'status': 'ok'})

    data = {'title': 'Типы платежей', 'pay_type': pay_type, 'sub_pay_types': sub_pay_types}

    return render(request, 'mainapp/payments_type.html', data)


'''не применяется'''
def payment_create_view(request):

    if request.method == 'POST':

        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                return JsonResponse(
                    {'message': False}
                )
            else:
                return JsonResponse(
                    {'message': True}
                )

        pay_type = request.POST.get('type_payment')
        PayType.objects.create(pay_type=pay_type)

        return redirect('pay_types')

    data = {
            'title': 'Создание типа платежа',
            'inside': {'page_url': 'pay-types', 'page_title': 'Типы платежей'},
            }
    return render(request, 'mainapp/payment_type_add.html', data)


def additional_data_transaction_view(request):
    additional = ''
    if request.user.is_superuser:
        additional = get_additional_transactions()
    else:
        additional = get_allow_additional_transactions(request.user.id)

    data = {'title': 'Дополнительные данные по транзакциям', 'additional': additional}

    return render(request, 'mainapp/additional_data_transactions.html', data)


def additional_transaction_data_create_view(request):
    transactions = ''
    if request.user.is_superuser:
        transactions = Transaction.objects.all().values('id', 'name')
    else:
        transactions = get_allow_transaction(request.user.id)
    if request.method == 'POST':
        if request.POST.get('type') == 'get_transaction_id':
            transaction_id = request.POST.get('transaction')
            result = set()

            for transaction in transactions:
                result.add(str(transaction_id) == f'{transaction.get("id")}: {transaction.get("name")}')

            if any(result):
                return JsonResponse(
                        {'message': True}
                    )
            else:
                return JsonResponse(
                    {'message': False}
                )

        transaction_id = Transaction.objects.filter(pk=request.POST.get('transaction')[0])[0]
        additional_data = request.POST.get('notes_transaction')

        AdditionalDataTransaction.objects.create(transaction_id=transaction_id, notes=additional_data)

        return redirect('additional_data')

    data = {'title': 'Создание дополнительных данных по транзакции', 'transactions': transactions,
            'inside': {'page_url': 'additional-data', 'page_title': 'Дополнительные данные по транзакциям '},
            }

    return render(request, 'mainapp/additional_data_transaction_create.html', data)


def lock_page(request):

    '''Для подтверждения Telegram_id'''
    md5_hash = md5(f'{request.user.id}_fv3353rv23v3ve_vsfvdfvdfvdf53f3_e1fj43d'.encode()).hexdigest()
    user_info = CustomUser.objects.filter(pk=request.user.id)
    data = {'title': 'Привязка Telegram аккаунта',  'md5_hash': md5_hash,
            'page_name': 'Доступ ограничен', 'lock_page': 'lock_page', 'user_info': user_info}

    return render(request, 'mainapp/lock-page.html', data)


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler403(request, exception):
    return render(request, '403.html', status=403)


def handler405(request, exception):
    return render(request, '405.html', status=405)


def handler500(request):
    return render(request, '500.html', status=500)


def handler501(request):
    return render(request, '501.html', status=501)
