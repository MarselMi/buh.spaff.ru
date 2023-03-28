from django.urls import path
from apiapp.views import *


urlpatterns = [
    path('users/', UserModelView.as_view(), name='main_page'),
    path('pay-type/', PayTypeModelView.as_view(), name='pay_type'),
    path('bal-holders/', BalanceHolderModelView.as_view(), name='b_holders'),
    path('transactions/', TransactionModelView.as_view(), name='transactions'),
    path('add-data-tr/', AdditionalDataTransactionModelView.as_view(), name='add_data_tr'),
    path('logs-transaction/', TransactionLogModelView.as_view(), name='logs_tr'),
]


