from urllib import request
from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView
from mainapp.models import Transaction, BalanceHolder, PayType, AdditionalDataTransaction
from django.views.generic.edit import FormView
from django.contrib.auth.decorators import login_required


class MainPageView(TemplateView):
    template_name = 'mainapp/main-page.html'


class TransactionsView(TemplateView):
    template_name = 'mainapp/transactions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = Transaction.objects.filter(deleted=False)
        # context['additional'] = AdditionalDataTransaction.objects.all()
        return context


class TransactionsCreateView(CreateView):

    template_name = 'mainapp/transaction_create.html'

    model = Transaction

    fields = [
        'name',
        'type_transaction',
        'description',
        'balance_holder',
        'amount',
        'type_payment',
        'tags',
    ]

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.save()
        return redirect('transactions')


class BalanceHolderView(ListView):
    template_name = 'mainapp/balance_holders.html'

    model = BalanceHolder

    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)


class BalanceHolderCreateView(CreateView):
    template_name = 'mainapp/balance_holder_create.html'

    model = BalanceHolder

    fields = [
        'holder_name',
        'holder',
        'holder_balance',
    ]

    def form_valid(self, form):
        form.save()
        return redirect('balance_holders')


class PaymentTypeView(TemplateView):
    template_name = 'mainapp/payments_type.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pay_type'] = PayType.objects.all()
        return context


class PaymentTypeCreateView(CreateView):
    template_name = 'mainapp/payment_type_add.html'

    model = PayType

    fields = [
        'pay_type'
    ]

    def form_valid(self, form):
        form.save()
        return redirect('pay_types')


class AdditionalDataTransactionView(TemplateView):
    template_name = 'mainapp/additional_data_transactions.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['additional'] = AdditionalDataTransaction.objects.filter(deleted=False)
        return context


class AdditionalDataTransactionCreateView(CreateView):
    template_name = 'mainapp/additional_data_transaction_create.html'

    model = AdditionalDataTransaction

    fields = [
        'transaction_id',
        'notes'
    ]

    def form_valid(self, form):
        form.save()
        return redirect('additional_data')