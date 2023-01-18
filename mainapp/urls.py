from django.urls import path
from .views import (
    MainPageView,
    TransactionsView,
    TransactionsCreateView,
    BalanceHolderCreateView,
    BalanceHolderView,
    PaymentTypeView,
    PaymentTypeCreateView,
    AdditionalDataTransactionView,
    AdditionalDataTransactionCreateView
)
from authapp.views import CustomLogoutView, CustomLoginView
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('', login_required(MainPageView.as_view(), login_url='login'), name='main_page'),

    # Авторизация и Выход
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # Транзакции
    path('transactions/', login_required(TransactionsView.as_view(), login_url='login'), name='transactions'),
    path('transactions-create/', login_required(TransactionsCreateView.as_view(), login_url='login'),
         name='transactions_create'),

    # Балансодержатели
    path('holders/', login_required(BalanceHolderView.as_view(), login_url='login'), name='balance_holders'),
    path('holder-create/', login_required(BalanceHolderCreateView.as_view(), login_url='login'),
         name='holder_create'),

    # Типы платежей
    path('pay-types/', login_required(PaymentTypeView.as_view(), login_url='login'), name='pay_types'),
    path('pay-create/', login_required(PaymentTypeCreateView.as_view(), login_url='login'), name='pay_create'),

    # Доп данные по транзакциям
    path('additional-data/', login_required(AdditionalDataTransactionView.as_view(), login_url='login'),
         name='additional_data'),
    path('addition-create/', login_required(AdditionalDataTransactionCreateView.as_view(), login_url='login'),
         name='addition_create'),
]

