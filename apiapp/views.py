from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from mainapp.data_library import *

from apiapp.serializers import (
    PayTypeSerializer,  BalanceHolderSerializer, CustomUserSerializer,
    TransactionSerializer, AdditionalDataTransactionSerializer,
    TransactionLogSerializer
)

from mainapp.models import (
    PayType, BalanceHolder, CustomUser, Transaction,
    AdditionalDataTransaction, TransactionLog
)


class UserModelView(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request, format=None):
        users = CustomUser.objects.all()
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)


class PayTypeModelView(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request):
        pay_type = PayType.objects.all()
        serializer = PayTypeSerializer(pay_type, many=True)
        return Response(serializer.data)


class BalanceHolderModelView(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request):
        if request.user.is_superuser:
            holders = get_allow_balance_holders(request.user.id, simple_user=False)
        else:
            holders = get_allow_balance_holders(request.user.id, simple_user=True)
        serializer = BalanceHolderSerializer(holders, many=True)
        return Response(serializer.data)


class TransactionModelView(APIView):

    renderer_classes = [JSONRenderer]

    def get(self, request):
        if request.user.is_superuser:
            transactions = get_allow_transaction_filter(request.user.id)
        else:
            transactions = get_allow_transaction_filter(request.user.id, author_res=True)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


# class TransactionViewSet(viewsets.ModelViewSet):
#
#     serializer_class = TransactionSerializer
#     queryset = Transaction.objects.all()
#
#     def list(self, request, *args, **kwargs):
#         if request.user.is_superuser:
#             queryset = get_allow_transaction_filter(request.user.id)
#         else:
#             queryset = get_allow_transaction_filter(request.user.id, author_res=True)
#         serializer = self.serializer_class(queryset, many=True)
#         return Response(serializer.data)


class AdditionalDataTransactionModelView(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request):
        if request.user.is_superuser:
            additional = AdditionalDataTransaction.objects.all()
        else:
            additional = get_allow_additional_transactions(request.user.id)
        serializer = AdditionalDataTransactionSerializer(additional, many=True)
        return Response(serializer.data)


class TransactionLogModelView(APIView):
    renderer_classes = [JSONRenderer]

    def get(self, request):
        transactions_log = TransactionLog.objects.all()

        serializer = TransactionLogSerializer(transactions_log, many=True)
        return Response(serializer.data)
