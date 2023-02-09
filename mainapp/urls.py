from django.urls import path
from authapp.views import CustomLogoutView, CustomLoginView, users_view, create_user_view, edit_user_view
from django.contrib.auth.decorators import login_required
from mainapp.views import (
    PaymentTypeCreateView,
    AdditionalDataTransactionCreateView, main_page_view,
    payment_type_view, additional_data_transaction_view, balance_holder_create_view, transactions_log_view,
    transaction_view, transaction_update_view, create_transaction_view,
    create_transaction_holder_view, balance_holders_views,
)

urlpatterns = [
    path('', login_required(main_page_view, login_url='login'),
         name='main_page'),

    # Авторизация, пользователи и Выход
    path('login/', CustomLoginView.as_view(),
         name='login'),
    path('users/', login_required(users_view, login_url='login'),
         name='users'),
    path('user-create/', login_required(create_user_view, login_url='login'),
         name='create_user'),
    path('user-edit/<int:pk>/', login_required(edit_user_view, login_url='login'),
         name='edit_user'),
    path('logout/', CustomLogoutView.as_view(),
         name='logout'),

    # Транзакции
    path('transactions/', login_required(transaction_view, login_url='login'),
         name='transactions'),
    path('transactions-create/', login_required(create_transaction_view, login_url='login'),
         name='transaction_create'),
    path('transactions-holder-create/<int:pk>', login_required(create_transaction_holder_view, login_url='login'),
         name='transactions_holder_create'),
    path('transaction-edit/<int:pk>/', login_required(transaction_update_view, login_url='login'),
         name='transaction_edit'),
    path('transactions-log/', login_required(transactions_log_view, login_url='login'),
         name='transactions_log'),

    # Балансодержатели
    path('holders/', login_required(balance_holders_views, login_url='login'),
         name='balance_holders'),
    path('holder-create/', login_required(balance_holder_create_view, login_url='login'),
         name='holder_create'),

    # Типы платежей
    path('pay-types/', login_required(payment_type_view, login_url='login'),
         name='pay_types'),
    path('pay-create/', login_required(PaymentTypeCreateView.as_view(), login_url='login'),
         name='pay_create'),

    # Доп данные по транзакциям
    path('additional-data/', login_required(additional_data_transaction_view, login_url='login'),
         name='additional_data'),
    path('addition-create/', login_required(AdditionalDataTransactionCreateView.as_view(), login_url='login'),
         name='addition_create'),
]
