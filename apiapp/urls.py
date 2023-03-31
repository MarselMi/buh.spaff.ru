from django.urls import path, include
from apiapp.views import *
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'transactions_view', TransactionCreateApi, basename='transactions')
router.register(r'users', UserModelView, basename='users')


urlpatterns = [
    path('', include(router.urls)),
    # path('users/', UserModelView.as_view(), name='users_api'),
    path('pay-types/', PayTypeModelView.as_view(), name='pay_type_api'),
    path('bal-holders/', BalanceHolderModelView.as_view(), name='b_holders_api'),
    # path('transactions-api/', TransactionModelView.as_view(), name='transactions_api'),
    path('add-data-tr/', AdditionalDataTransactionModelView.as_view(), name='add_data_tr_api'),
    path('logs-transaction/', TransactionLogModelView.as_view(), name='logs_tr_api'),
]


