from django.urls import path
from authapp.views import CustomLogoutView, CustomLoginView, custom_login
from django.contrib.auth.decorators import login_required
from .views import (
    TransactionsView, TransactionsCreateView, BalanceHolderCreateView,
    BalanceHolderView, PaymentTypeCreateView,
    AdditionalDataTransactionCreateView,
    handler404, handler403, handler405, handler500, handler501, TransactionUpdateView, main_page_view,
    payment_type_view, additional_data_transaction_view,
)


urlpatterns = [
    path('', login_required(main_page_view, login_url='login'), name='main_page'),

    # Авторизация и Выход
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # Транзакции
    path('transactions/', login_required(TransactionsView.as_view(), login_url='login'), name='transactions'),
    path('transactions-create/', login_required(TransactionsCreateView.as_view(), login_url='login'),
         name='transaction_create'),
    path('transaction-edit/<int:pk>/', login_required(TransactionUpdateView.as_view(), login_url='login'),
         name='transaction_edit'),

    # Балансодержатели
    path('holders/', login_required(BalanceHolderView.as_view(), login_url='login'), name='balance_holders'),
    path('holder-create/', login_required(BalanceHolderCreateView.as_view(), login_url='login'),
         name='holder_create'),

    # Типы платежей
    path('pay-types/', login_required(payment_type_view, login_url='login'), name='pay_types'),
    path('pay-create/', login_required(PaymentTypeCreateView.as_view(), login_url='login'), name='pay_create'),

    # Доп данные по транзакциям
    path('additional-data/', login_required(additional_data_transaction_view, login_url='login'),
         name='additional_data'),
    path('addition-create/', login_required(AdditionalDataTransactionCreateView.as_view(), login_url='login'),
         name='addition_create'),
]

handler404 = handler404
handler403 = handler403
handler405 = handler405
handler500 = handler500
handler501 = handler501
