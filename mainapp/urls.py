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


urlpatterns = [
    path('', MainPageView.as_view(), name='main_page'),

    # Авторизация и Выход
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    # Транзакции
    path('transactions/', TransactionsView.as_view(), name='transactions'),
    path('transactions-create/', TransactionsCreateView.as_view(), name='transactions_create'),

    # Балансодержатели
    path('holders/', BalanceHolderView.as_view(), name='balance_holders'),
    path('holder-create/', BalanceHolderCreateView.as_view(), name='holder_create'),

    # Типы платежей
    path('pay-types/', PaymentTypeView.as_view(), name='pay_types'),
    path('pay-create/', PaymentTypeCreateView.as_view(), name='pay_create'),

    # Доп данные по транзакциям
    path('additional-data/', AdditionalDataTransactionView.as_view(), name='additional_data'),
    path('addition-create/', AdditionalDataTransactionCreateView.as_view(), name='addition_create'),
]

