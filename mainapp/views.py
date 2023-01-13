from django.views.generic import TemplateView


class MainPageView(TemplateView):
    template_name = 'mainapp/main-page.html'


class TransactionsView(TemplateView):
    template_name = 'mainapp/transactions.html'


class TransactionsCreateView(TemplateView):
    template_name = 'mainapp/transaction_create.html'


class BalanceHolderView(TemplateView):
    template_name = 'mainapp/balance_holders.html'


class BalanceHolderCreateView(TemplateView):
    template_name = 'mainapp/balance_holder_create.html'


class PaymentTypeView(TemplateView):
    template_name = 'mainapp/payments_type.html'


class PaymentTypeCreateView(TemplateView):
    template_name = 'mainapp/payment_type_add.html'


class AdditionalDataTransactionView(TemplateView):
    template_name = 'mainapp/additional_data_transactions.html'


class AdditionalDataTransactionCreateView(TemplateView):
    template_name = 'mainapp/additional_data_transaction_create.html'