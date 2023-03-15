from rest_framework.serializers import HyperlinkedModelSerializer
from mainapp.models import *
from rest_framework import serializers


class PayTypeSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = PayType
        fields = '__all__'


class BalanceHolderSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = BalanceHolder
        fields = '__all__'


class CustomUserSerializer(HyperlinkedModelSerializer):

    available_holders = serializers.StringRelatedField(many=True)

    class Meta:
        model = CustomUser
        fields = '__all__'


class TransactionSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class AdditionalDataTransactionSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = AdditionalDataTransaction
        fields = '__all__'


class TransactionLogSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = TransactionLog
        fields = '__all__'
