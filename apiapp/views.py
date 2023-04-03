import decimal
import json
from datetime import datetime as dt
from rest_framework.views import APIView
from rest_framework import viewsets, status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from mainapp.data_library import *
from apiapp.serializers import *
from mainapp.models import *


class UserModelView(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer


class SubPayTypeApiView(viewsets.ModelViewSet):
    queryset = SubPayType.objects.all()
    serializer_class = SubPayTypeSerializer


class PayTypeModelView(viewsets.ModelViewSet):

    queryset = PayType.objects.all()
    serializer_class = PayTypeSerializer


class BalanceHolderModelView(viewsets.ModelViewSet):

    queryset = BalanceHolder.objects.all()
    serializer_class = BalanceHolderSerializer
    users = CustomUser.objects.all()
    user_serializer = CustomUserSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.filter_queryset()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class TransactionCreateApi(viewsets.ModelViewSet):

    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        user_info = CustomUser.objects.get(pk=self.request.data.get('author_id'))

        if user_info.is_superuser:
            balance_holders = BalanceHolder.objects.all()
        else:
            balance_holders = user_info.available_holders.all()

        holder_response = self.request.data.get('balance_holder')
        balance_holder_response = balance_holders.get(organization_holder=holder_response)
        sub_type = None
        if self.request.data.get('sub_type'):
            sub_type = SubPayType.objects.filter(sub_type=self.request.data.get('sub_type'))[0].pk
        name = self.request.data.get('transaction_name')
        status_tr = self.request.data.get('transaction_status')
        if status_tr == 'В процессе':
            status_tr = 'INPROCESS'
        elif status_tr == 'Отклонен':
            status_tr = 'REJECT'
        else:
            status_tr = 'SUCCESSFULLY'

        transaction_date = dt.strptime(self.request.data.get('transaction_date'), '%d.%m.%Y').date()

        type_payment = PayType.objects.filter(pay_type=self.request.data.get('type_payment'))[0].pk

        commission = 0
        if self.request.data.get('commission_post'):
            commission = decimal.Decimal(self.request.data.get('commission_post').replace(',', '.').replace(' ', ''))
        transaction_sum = decimal.Decimal(self.request.data.get('transaction_sum_post').replace(',', '.').replace(' ', ''))

        type_transaction = self.request.data.get('type_transaction')
        if type_transaction == 'Приход':
            type_transaction = 'COMING'
            amount = transaction_sum
            commission = 0
        else:
            type_transaction = 'EXPENDITURE'
            amount = transaction_sum + commission

        '''Логика для загрузки ЧЕКов'''
        image = self.request.FILES.get('check_img')
        if image:
            check_img = f"img/{str(image).replace(' ', '_')}"
            root = f'{settings.MEDIA_ROOT}/{str(check_img)}'
            with open(root, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)
            image = check_img

        description = self.request.data.get('description')
        tags = self.request.data.get('tags')
        author_id = user_info.id

        new_data = {
            'transaction_date': transaction_date, 'type_transaction': type_transaction,
            'name': name, 'description': description, 'balance_holder': balance_holder_response.pk,
            'amount': amount, 'type_payment': type_payment, 'status': status_tr, 'tags': tags,
            'check_img': image, 'author': author_id, 'commission': commission, 'transaction_sum': transaction_sum,
            'sub_type_pay': sub_type
        }

        old_balance_balance_holder = balance_holder_response.holder_balance
        if status == 'SUCCESSFULLY':
            if type_transaction == 'COMING':
                old_balance_balance_holder += amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
            else:
                old_balance_balance_holder -= amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
        else:
            pass

        serializer = self.get_serializer(data=new_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TransactionModelView(viewsets.ModelViewSet):
    def list(self, request, *args, **kwargs):
        if request.user.is_superuser:
            queryset = Transaction.objects.all()
        else:
            queryset = Transaction.objects.all()
        serializer = TransactionSerializer(queryset, many=True)
        return Response(serializer.data)


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
