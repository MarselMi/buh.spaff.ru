from urllib import request
from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from apiapp.serializers import (
    PayTypeSerializer,  BalanceHolderSerializer, CustomUserSerializer,
    TransactionSerializer, AdditionalDataTransactionSerializer,
    TransactionLogSerializer
)
from mainapp.models import (
    PayType, BalanceHolder, CustomUser, Transaction,
    AdditionalDataTransaction, TransactionLog
)


class UserModelView(ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer


class PayTypeModelView(ModelViewSet):
    queryset = PayType.objects.all()
    serializer_class = PayTypeSerializer


class BalanceHolderModelView(ModelViewSet):
    queryset = BalanceHolder.objects.all()
    serializer_class = BalanceHolderSerializer


class TransactionModelView(ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


class AdditionalDataTransactionModelView(ModelViewSet):
    queryset = AdditionalDataTransaction.objects.all()
    serializer_class = AdditionalDataTransactionSerializer


class TransactionLogModelView(ModelViewSet):
    queryset = TransactionLog.objects.all()
    serializer_class = TransactionLogSerializer
