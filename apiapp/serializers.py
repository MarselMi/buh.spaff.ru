from rest_framework.serializers import ModelSerializer
from mainapp.models import *


class PayTypeSerializer(ModelSerializer):
    class Meta:
        model = PayType
        fields = '__all__'


class BalanceHolderSerializer(ModelSerializer):
    class Meta:
        model = BalanceHolder
        fields = '__all__'


class CustomUserSerializer(ModelSerializer):

    class Meta:
        model = CustomUser
        fields = '__all__'


class TransactionSerializer(ModelSerializer):

    class Meta:
        model = Transaction
        fields = '__all__'


class AdditionalDataTransactionSerializer(ModelSerializer):

    class Meta:
        model = AdditionalDataTransaction
        fields = '__all__'


class TransactionLogSerializer(ModelSerializer):
    class Meta:
        model = TransactionLog
        fields = '__all__'
