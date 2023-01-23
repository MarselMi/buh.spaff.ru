from urllib import request
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView
from datetime import datetime as dt
from mainapp.forms import (
    TransactionForm, BalanceHolderForm, AdditionalDataTransactionForm,
    PayTypeForm, TransactionUpdateForm
)
from mainapp.mixin import SuperuserRequiredMixin
from mainapp.models import (
    Transaction, BalanceHolder, PayType, AdditionalDataTransaction,
    TransactionLog
)
from django.views.generic.edit import UpdateView


class MainPageView(TemplateView):
    template_name = 'mainapp/main-page.html'

    extra_context = {'title': 'Главная страница'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['holders'] = BalanceHolder.objects.filter(deleted=False)
        context['transactions'] = Transaction.objects.filter(balance_holder=1, status='SUCCESSFULLY')
        return context


class TransactionsView(TemplateView):
    template_name = 'mainapp/transactions.html'
    extra_context = {'title': 'Транзакции'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = Transaction.objects.filter(deleted=False)
        context['transactions'] = context['transactions'][::-1]
        return context


class TransactionsCreateView(CreateView):

    template_name = 'mainapp/transaction_create.html'
    model = Transaction
    form_class = TransactionForm
    extra_context = {'title': 'Создание транзакции',
                     'inside': {
                         'page_url': 'transactions',
                         'page_title': 'Транзакции'
                     }}

    def form_valid(self, form):
        form.save(commit=False)
        form.instance.author = self.request.user
        id_balance_holder = form.instance.balance_holder.id
        balance_hodler = BalanceHolder.objects.filter(pk=id_balance_holder)
        balance = balance_hodler.values_list('holder_balance', flat=True).get(pk=id_balance_holder)

        if form.instance.type_transaction == 'COMING':
            balance += form.instance.amount
        else:
            balance -= form.instance.amount

        BalanceHolder.objects.filter(pk=id_balance_holder).update(holder_balance=balance)
        form.save()

        return redirect('transactions')


class TransactionUpdateView(SuperuserRequiredMixin, UpdateView):
    template_name = 'mainapp/transaction_edit.html'
    model = Transaction
    form_class = TransactionUpdateForm
    extra_context = {'title': 'Изменение транзакции',
                     'inside': {
                         'page_url': 'transactions',
                         'page_title': 'Транзакции'
                     }}

    def form_valid(self, form):

        transaction = form.save(commit=False)

        changes = {
            'transaction_id': transaction.id,
            'author_references': self.request.user
        }

        old_transaction = self.model.objects.filter(pk=transaction.id).values(
            'status', 'transaction_date', 'amount', 'description', 'type_payment', 'check_img'
        )

        id_balance_holder = form.instance.balance_holder.id
        balance_hodler = BalanceHolder.objects.filter(pk=id_balance_holder)
        old_balance_holder = balance_hodler.values('holder_balance')[0]['holder_balance']

        for k in old_transaction[0]:
            check = eval(f'transaction.{k}') == old_transaction[0][k]
            if not check:
                changes[k] = str(old_transaction[0][k])+"/"+str(eval(f'transaction.{k}'))
        if len(changes.values()) > 2:
            TransactionLog.objects.create(**changes)
        transaction.update_date = dt.now()

        if old_transaction[0]['amount'] > transaction.amount:
            change = old_transaction[0]['amount'] - transaction.amount
            if self.model.objects.filter(pk=transaction.id).values('type_transaction')[0]['type_transaction'] == 'COMING':
                old_balance_holder -= change
                balance_hodler.update(holder_balance=old_balance_holder)
            else:
                old_balance_holder += change
                balance_hodler.update(holder_balance=old_balance_holder)
        elif old_transaction[0]['amount'] < transaction.amount:
            change = transaction.amount - old_transaction[0]['amount']
            if self.model.objects.filter(pk=transaction.id).values('type_transaction')[0]['type_transaction'] == 'COMING':
                old_balance_holder += change
                balance_hodler.update(holder_balance=old_balance_holder)
            else:
                old_balance_holder -= change
                balance_hodler.update(holder_balance=old_balance_holder)
        else:
            pass

        form.save()

        return redirect('transactions')


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


class PaymentTypeView(TemplateView):
    template_name = 'mainapp/payments_type.html'
    extra_context = {'title': 'Типы платежей'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pay_type'] = PayType.objects.all()
        return context


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


class AdditionalDataTransactionView(TemplateView):
    template_name = 'mainapp/additional_data_transactions.html'
    extra_context = {'title': 'Дополнительные данные по транзакциям'}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['additional'] = AdditionalDataTransaction.objects.filter(deleted=False)
        return context


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
    return render(request, 'mainapp/404.html', status=404)


def handler403(request, exception):
    return render(request, 'mainapp/403.html', status=403)


def handler405(request, exception):
    return render(request, 'mainapp/405.html', status=405)


def handler500(request):
    return render(request, 'mainapp/500.html', status=500)


def handler501(request):
    return render(request, 'mainapp/501.html', status=501)