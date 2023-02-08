import json
import decimal
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView
from datetime import datetime as dt

from mainapp.data_library import *
from mainapp.forms import (
    TransactionForm, BalanceHolderForm, AdditionalDataTransactionForm,
    PayTypeForm, TransactionUpdateForm
)
from mainapp.models import (
    Transaction, BalanceHolder, PayType, AdditionalDataTransaction,
    TransactionLog
)


def main_page_view(request):

    holders = BalanceHolder.objects.filter(deleted=False)

    type_payments = PayType.objects.all()

    if request.method == 'POST':
        if request.POST.get('type') == 'holders_id':

            transaction_id = request.POST.get('id')

            transactions = get_transaction_holder(transaction_id)

            for transaction in transactions:
                transaction['create_date'] = transaction['create_date'].strftime('%d.%m.%Y в %H:%M:%S')
                if transaction.get('update_date'):
                    transaction['update_date'] = transaction['update_date'].strftime('%d.%m.%Y')
                transaction['transaction_date'] = transaction['transaction_date'].strftime('%d.%m.%Y')
                if round(transaction['amount'], 2) % 1 == 0:
                    transaction['amount'] = '{0:,}'.format(int(transaction['amount'])).replace(',', ' ')
                else:
                    transaction['amount'] = round(transaction['amount'], 2)
                    transaction['amount'] = '{0:,}'.format(transaction['amount']).replace(',', ' ').replace('.', ',')

            sum_coming_obj = get_coming_sum(transaction_id)
            sum_expenditure_obj = get_expenditure_sum(transaction_id)
            sum_coming = {}
            sum_expenditure = {}
            balance_holder = BalanceHolder.objects.filter(pk=transaction_id).values('organization_holder')[0]['organization_holder']

            sum_coming['coming'] = numb_format(sum_coming_obj[0]['coming'])
            sum_expenditure['expenditure'] = numb_format(sum_expenditure_obj[0]['expenditure'])

            result = {
                'transactions': transactions,
                'sum_coming': sum_coming,
                'sum_expenditure': sum_expenditure,
                'balance_holder': balance_holder
            }
            return HttpResponse(json.dumps(result))

        if request.POST.get('type') == 'create_transaction':

            holder = BalanceHolder.objects.filter(organization_holder=request.POST.get('holder_post'))[0]

            transaction_name = request.POST.get('transaction_name_post')

            transaction_date = dt.strptime(request.POST.get('transaction_date_post'), '%d.%m.%Y').date()
            amount = decimal.Decimal(request.POST.get('amount_post').replace(',', '.').replace(' ', ''))
            payment_type = PayType.objects.filter(pay_type=request.POST.get('payment_type_post'))[0]

            transaction_type = request.POST.get('transaction_type_post')
            if transaction_type == 'Приход':
                transaction_type = 'COMING'
            else:
                transaction_type = 'EXPENDITURE'

            author_id = request.user.id

            create_data = {'type_transaction': transaction_type,
                           'transaction_date': transaction_date,
                           'name': transaction_name,
                           'balance_holder': holder,
                           'amount': amount,
                           'type_payment': payment_type,
                           'author_id': author_id
                           }

            transaction = Transaction

            transaction.objects.create(**create_data)
            print(create_data)
            return HttpResponse(json.dumps({"Status": "OK"}))

    color_list = ['primary', 'secondary', 'success', 'info', 'light', 'danger', 'warning', 'dark']

    data = {'title': 'Главная страница', 'holders': holders, 'color_list': color_list, 'type_payments': type_payments,
            }

    return render(request, 'mainapp/main-page.html', data)


def transaction_view(request):
    transactions = Transaction.objects.filter(deleted=False)[::-1]
    data = {'title': 'Транзакции',
            'transactions': transactions}
    return render(request, 'mainapp/transactions.html', data)


def create_transaction_view(request):

    transaction = Transaction
    form = TransactionForm
    type_payments = PayType.objects.all()
    balance_holders = BalanceHolder.objects.all()

    if request.method == 'POST':
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

        amount = decimal.Decimal(request.POST.get('amount').replace(',', '.').replace(' ', ''))

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

        new_data = {'transaction_date': transaction_date, 'type_transaction': type_transaction,
                    'name': name, 'description': description, 'balance_holder': balance_holder_response[0],
                    'amount': amount, 'type_payment': type_payment, 'status': status, 'tags': tags,
                    'check_img': image, 'author_id': author_id}

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

        amount = decimal.Decimal(request.POST.get('amount').replace(',', '.').replace(' ', ''))

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

        new_data = {'transaction_date': transaction_date, 'type_transaction': type_transaction,
                    'name': name, 'description': description, 'balance_holder': balance_holder_response[0],
                    'amount': amount, 'type_payment': type_payment, 'status': status, 'tags': tags,
                    'check_img': image, 'author_id': author_id}

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

    old_transaction = transaction.values(
        'status', 'transaction_date', 'amount', 'description', 'type_payment', 'check_img'
    )

    if request.method == 'POST':

        status = request.POST.get('transaction_status')
        if status == 'В процессе':
            status = 'INPROCESS'
        elif status == 'Отклонен':
            status = 'REJECT'
        else:
            status = 'SUCCESSFULLY'

        '''Данные через форму'''
        transaction_date = dt.strptime(request.POST.get('transaction_date'), '%d.%m.%Y').date()
        amount = decimal.Decimal(request.POST.get('amount').replace(',', '.').replace(' ', ''))
        type_payment = PayType.objects.filter(pay_type=request.POST.get('type_payment'))[0].pk

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

        description = request.POST.get('description')
        tags = request.POST.get('tags')

        '''Словарь новых данных по форме'''
        new_transaction_data = {'status': status, 'transaction_date': transaction_date,
                                'amount': amount, 'type_payment': type_payment, 'check_img': check_img,
                                'tags': tags, 'description': description}

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

        if status == 'SUCCESSFULLY':
            if Transaction.objects.filter(pk=transaction[0].id).values('type_transaction')[0]['type_transaction'] == 'COMING':
                old_balance_balance_holder += transaction[0].amount
                balance_hodler.update(holder_balance=old_balance_balance_holder)
            else:
                old_balance_balance_holder -= transaction[0].amount
                balance_hodler.update(holder_balance=old_balance_balance_holder)
        else:
            pass

        transaction.update(**new_transaction_data)

        return redirect('transactions')

    data = {'title': 'Изменение транзакции', 'inside': {'page_url': 'transactions', 'page_title': 'Транзакции'},
            'form': form_class, 'transaction': transaction[0], 'type_payments': type_payments}

    return render(request, 'mainapp/transaction_edit.html', data)


def transactions_log_view(request):
    transactions_log = TransactionLog.objects.all()
    data = {'title': 'Логи транзакций', 'transactions_log': transactions_log}
    return render(request, 'mainapp/transactions_log.html', data)


class BalanceHolderView(ListView):
    template_name = 'mainapp/balance_holders.html'
    extra_context = {'title': 'Балансодержатели'}
    model = BalanceHolder

    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)


class BalanceHolderCreateView(CreateView):
    template_name = 'mainapp/balance_holder_create.html'
    extra_context = {'title': 'Создание балансодержателя',
                     'inside': {
                         'page_url': 'holders',
                         'page_title': 'Балансодержатели '
                     }}
    model = BalanceHolder
    form_class = BalanceHolderForm

    def form_valid(self, form):
        form.save()
        return redirect('balance_holders')


def balance_holder_create_view(request):

    model = BalanceHolder
    form_class = BalanceHolderForm

    data = {'title': 'Создание балансодержателя',
            'inside': {
                'page_url': 'holders',
                'page_title': 'Балансодержатели '
                },
            'form': form_class,
            }

    if request.method == 'POST':
        name = request.POST.get('')
        return redirect('balance_holders')

    return render(request, 'mainapp/balance_holder_create.html', data)


def payment_type_view(request):
    pay_type = PayType.objects.all()

    data = {'title': 'Типы платежей', 'pay_type': pay_type}

    return render(request, 'mainapp/payments_type.html', data)


class PaymentTypeCreateView(CreateView):
    template_name = 'mainapp/payment_type_add.html'
    extra_context = {'title': 'Создание типа платежа',
                     'inside': {
                         'page_url': 'pay-types',
                         'page_title': 'Типы платежей'
                     }}
    model = PayType
    form_class = PayTypeForm

    def form_valid(self, form):
        form.save()
        return redirect('pay_types')


def additional_data_transaction_view(request):
    additional = AdditionalDataTransaction.objects.filter(deleted=False).values('notes', 'transaction_id__name')

    data = {'title': 'Дополнительные данные по транзакциям', 'additional': additional}
    return render(request, 'mainapp/additional_data_transactions.html', data)


class AdditionalDataTransactionCreateView(CreateView):
    template_name = 'mainapp/additional_data_transaction_create.html'
    extra_context = {'title': 'Создание дополнительных данных по транзакции',
                     'inside': {
                         'page_url': 'additional-data',
                         'page_title': 'Дополнительные данные по транзакциям '
                     }}
    model = AdditionalDataTransaction
    form_class = AdditionalDataTransactionForm

    def form_valid(self, form):
        form.save()
        return redirect('additional_data')


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
