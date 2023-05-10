from __future__ import absolute_import, unicode_literals
from spaffaccaunting.celery import app
from datetime import datetime as dt
from mainapp.models import ImportData, BalanceHolder, Transaction, PayType, SubPayType
import requests
import json
from decimal import Decimal


@app.task
def import_transactions():
    objects_active = ImportData.objects.filter(status_import=True)
    for obj in objects_active:
        date_start = obj.date_start.strftime('%Y-%m-%d')
        date_end = dt.now().date()
        inn = obj.inn
        user_id = int(obj.author)

        transactions_objects = json.loads(requests.get(
            f"https://business.tinkoff.ru/openapi/api/v1/bank-statement?accountNumber={obj.account}&from={date_start}&till={date_end}",
            headers={'Authorization': f'Bearer {obj.key}'}
        ).content).get('operation')

        for transaction in transactions_objects:
            transaction_new = Transaction
            sub_type = None
            if len(Transaction.objects.filter(import_id=transaction.get('operationId'))) == 0:
                if transaction.get('paymentPurpose').lower().find('cloudpayments') > -1:
                    pay_type = PayType.objects.filter(pay_type='CloudPayments')
                elif transaction.get('paymentPurpose').find('№230583') > -1:
                    pay_type = PayType.objects.filter(pay_type='Селектел')
                elif transaction.get('paymentPurpose').lower().find('плата за') > -1:
                    pay_type = PayType.objects.filter(pay_type='Услуги Банка')
                    if ((transaction.get('paymentPurpose').lower().find('sms-банк') > -1) or (transaction.get('paymentPurpose').lower().find('оповещение') > -1)):
                        sub_type = SubPayType.objects.filter(sub_type='SMS-оповещение')
                    elif transaction.get('paymentPurpose').lower().find('обслуживание счета') > -1:
                        sub_type = SubPayType.objects.filter(sub_type='Обслуживание счета')
                    elif transaction.get('paymentPurpose').lower().find('межбанки') > -1:
                        sub_type = SubPayType.objects.filter(sub_type='Межбанки без комиссий')
                elif transaction.get('paymentPurpose').lower().find('овердрафт') > -1:
                    pay_type = PayType.objects.filter(pay_type='Услуги Банка')
                    sub_type = SubPayType.objects.filter(sub_type='Овердрафт')
                elif ((transaction.get('paymentPurpose').lower().find('комиссия за внешний') > -1) or (transaction.get('paymentPurpose').lower().find('комиссия за ') > -1)):
                    pay_type = PayType.objects.filter(pay_type='Услуги банка')
                    sub_type = SubPayType.objects.filter(sub_type='Комиссия за внешние переводы')
                elif ((transaction.get('paymentPurpose').lower().find('зарплата') > -1) or (transaction.get('paymentPurpose').lower().find('заработной') > -1)):
                    pay_type = PayType.objects.filter(pay_type='Зарплата')
                elif transaction.get('paymentPurpose').lower().find('взносы') > -1:
                    pay_type = PayType.objects.filter(pay_type='Взносы')
                elif ((transaction.get('paymentPurpose').lower().find('оплата') >= 0) or (transaction.get('paymentPurpose').lower().find('платеж по сч') >= 0)):
                    pay_type = PayType.objects.filter(pay_type='Прочие')
                elif transaction.get('paymentPurpose').lower().find('платеж') > -1:
                    if int(transaction.get('amount')) == 7800 or int(transaction.get('amount')) == 15600:
                        pay_type = PayType.objects.filter(pay_type='НДФЛ')
                    elif (transaction.get('paymentPurpose').lower().find('налоговый') > -1) or (transaction.get('paymentPurpose').lower().find('аванс') > -1):
                        pay_type = PayType.objects.filter(pay_type='Налоги')
                elif transaction.get('paymentPurpose').lower().find('налог на ') > -1:
                    pay_type = PayType.objects.filter(pay_type='Налоги')
                elif transaction.get('paymentPurpose').lower().find('ндфл') > -1:
                    if int(transaction.get('amount')) == 7800 or int(transaction.get('amount')) == 15600:
                        pay_type = PayType.objects.filter(pay_type='НДФЛ')
                    else:
                        pay_type = PayType.objects.filter(pay_type='Налоги')
                elif ((transaction.get('paymentPurpose').lower().find('перевод средств') > -1) or (transaction.get('paymentPurpose').lower().find('перевод с карты') > -1)):
                    pay_type = PayType.objects.filter(pay_type='Пополнение')
                elif transaction.get('paymentPurpose').lower().find('аванс ') > -1:
                    pay_type = PayType.objects.filter(pay_type='Аванс')
                else:
                    pay_type = PayType.objects.filter(pay_type='Временная категория')

                if transaction.get('payerInn') == inn:
                    type_transaction = 'EXPENDITURE'
                    import_id = transaction.get('operationId')
                    balance_holder = BalanceHolder.objects.filter(organization_holder=obj.balance_holder)
                    tr_name = f"{transaction.get('paymentPurpose')[:28]}..."
                    status = 'SUCCESSFULLY'
                    transaction_date = dt.strptime(transaction.get('date'), '%Y-%m-%d').date()
                    amount = Decimal(transaction.get('amount'))
                    description = transaction.get('paymentPurpose')
                    if sub_type:
                        new_data = {
                            'transaction_date': transaction_date, 'type_transaction': type_transaction,
                            'name': tr_name, 'description': description, 'balance_holder': balance_holder[0],
                            'amount': amount, 'status': status, 'author_id': user_id, 'transaction_sum': amount,
                            'import_id': import_id, 'type_payment': pay_type[0], 'sub_type_pay': sub_type[0]
                        }
                    else:
                        new_data = {
                            'transaction_date': transaction_date, 'type_transaction': type_transaction,
                            'name': tr_name, 'description': description, 'balance_holder': balance_holder[0],
                            'amount': amount, 'status': status, 'author_id': user_id, 'transaction_sum': amount,
                            'import_id': import_id, 'type_payment': pay_type[0]
                        }

                    transaction_new.objects.create(**new_data)

                    old_balance_balance_holder = balance_holder[0].holder_balance
                    old_balance_balance_holder -= amount
                    balance_holder.update(holder_balance=old_balance_balance_holder)
                else:
                    type_transaction = 'COMING'
                    import_id = transaction.get('operationId')
                    balance_holder = BalanceHolder.objects.filter(
                        organization_holder=obj.balance_holder
                    )
                    tr_name = f"{transaction.get('paymentPurpose')[:28]}..."
                    status = 'SUCCESSFULLY'
                    transaction_date = dt.strptime(transaction.get('date'), '%Y-%m-%d').date()
                    amount = Decimal(transaction.get('amount'))
                    description = transaction.get('paymentPurpose')
                    if sub_type:
                        new_data = {
                            'transaction_date': transaction_date, 'type_transaction': type_transaction,
                            'name': tr_name, 'description': description, 'balance_holder': balance_holder[0],
                            'amount': amount, 'status': status, 'author_id': user_id, 'transaction_sum': amount,
                            'import_id': import_id, 'type_payment': pay_type[0], 'sub_type_pay': sub_type[0]
                        }
                    else:
                        new_data = {
                            'transaction_date': transaction_date, 'type_transaction': type_transaction,
                            'name': tr_name, 'description': description, 'balance_holder': balance_holder[0],
                            'amount': amount, 'status': status, 'author_id': user_id, 'transaction_sum': amount,
                            'import_id': import_id, 'type_payment': pay_type[0]
                        }
                    transaction_new.objects.create(**new_data)

                    old_balance_balance_holder = balance_holder[0].holder_balance

                    old_balance_balance_holder += amount
                    balance_holder.update(holder_balance=old_balance_balance_holder)
            else:
                pass
