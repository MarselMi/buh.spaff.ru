from __future__ import absolute_import, unicode_literals
import decimal
from spaffaccaunting.celery import app
from datetime import datetime as dt
import datetime
from mainapp.models import ImportData, BalanceHolder, Transaction, PayType, SubPayType
import requests
import json
from decimal import Decimal


@app.task
def import_transactions():
    objects_active = ImportData.objects.filter(status_import=True)
    for obj in objects_active:
        user_id = int(obj.author)
        balance_holder = BalanceHolder.objects.filter(organization_holder=obj.balance_holder)
        if obj.bank == 'tinkoff':
            date_start = obj.date_start.strftime('%Y-%m-%d')
            if obj.repyt_start_date:
                date_start = obj.repyt_start_date.strftime('%Y-%m-%d')
            date_end = dt.now().date()
            inn = obj.inn
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
        elif obj.bank == 'capitalist':
            date_start = obj.date_start.strftime('%d.%m.%Y')
            if obj.repyt_start_date:
                date_start = obj.repyt_start_date.strftime('%d.%m.%Y')
            password = obj.key
            login = obj.account
            token_request = (requests.post(
                'https://api.capitalist.net/',
                json={"operation": "get_token", "login": login},
                headers={"x-response-format": "json"})
            )

            token = json.loads(token_request.content).get('data').get('token')

            transactions_history = requests.post(
                'https://api.capitalist.net/',
                json={
                    "operation": "get_documents_history_ext",
                    "login": login,
                    "token": token,
                    "plain_password": password,
                    "document_state": "executed",
                    "limit": 100,
                    "period_from": date_start
                },
                headers={"x-response-format": "json"}
            )
            currency_rates_req = json.loads(requests.post(
                'https://api.capitalist.net/',
                json={"operation": "currency_rates", "login": login, "token": token, "plain_password": password},
                headers={"x-response-format": "json"}
            ).content).get('data').get('rates')
            currency_usd = 0
            currency_eur = 0
            currency_eth_usd = 0
            for i in currency_rates_req.get('sell'):
                if i.get('target') == 'EUR' and i.get('amountCur') == 'RUR':
                    currency_eur = i.get('amount')
                if i.get('target') == 'USD' and i.get('amountCur') == 'RUR':
                    currency_usd = i.get('amount')
                if i.get('target') == 'ETH' and i.get('amountCur') == 'USD':
                    currency_eth_usd = i.get('amount')
            currency_eth = currency_eth_usd * currency_usd
            page_count = int(json.loads(transactions_history.content).get('data').get('pages').get('pageCount'))
            if page_count == 1:
                transactions = json.loads(transactions_history.content).get('data').get('history')
                for i in transactions:
                    if len(Transaction.objects.filter(import_id=i.get('id'))) == 0:
                        old_balance_balance_holder = balance_holder[0].holder_balance
                        new_transa = Transaction
                        if i.get('outgoing') and i.get('selfExchange') is False:
                            current = None
                            current_sum = None
                            type_payment = PayType.objects.filter(pay_type='Выплаты-партнерские')[0]
                            tr_comis = i.get('tax')
                            if i.get('account')[0] == 'H':
                                current_sum = i.get('amount')
                                current = 'ETH'
                                tr_comis *= currency_eth
                                tr_sum = i.get('amount') * currency_eth
                                amount = tr_sum + tr_comis
                            elif i.get('account')[0] == 'U':
                                current_sum = i.get('amount')
                                current = 'USD'
                                tr_comis *= currency_usd
                                tr_sum = i.get('amount') * currency_usd
                                amount = tr_sum + tr_comis
                            elif i.get('account')[0] == 'T':
                                current_sum = i.get('amount')
                                current = 'USDT'
                                tr_comis *= currency_usd
                                tr_sum = i.get('amount') * currency_usd
                                amount = tr_sum + tr_comis
                            elif i.get('account')[0] == 'E':
                                current_sum = i.get('amount')
                                current = 'EUR'
                                tr_comis *= currency_eur
                                tr_sum = i.get('amount') * currency_eur
                                amount = tr_sum + tr_comis
                            else:
                                tr_sum = i.get('amount')
                                amount = tr_sum + tr_comis
                            new_data = {
                                'transaction_date': dt.fromtimestamp(int(i.get('timestamp'))), 'type_transaction': 'EXPENDITURE',
                                'name': f'Capital_{i.get("number")}', 'description': i.get('description'), 'balance_holder': balance_holder[0],
                                'amount': amount, 'status': 'SUCCESSFULLY', 'author_id': 1, 'transaction_sum': tr_sum,
                                'import_id': i.get('id'), 'type_payment': type_payment, 'commission': tr_comis, 'current_transaction': current,
                                'current_sum': current_sum, 'current_amount': i.get('amount') + i.get('tax')
                            }
                            new_transa.objects.create(**new_data)
                            old_balance_balance_holder -= decimal.Decimal(amount)
                            balance_holder.update(holder_balance=old_balance_balance_holder)
                        elif i.get('outgoing') is False and i.get('selfExchange') is False:
                            current = None
                            current_sum = None
                            type_payment = PayType.objects.filter(pay_type='Пополнение')[0]
                            if i.get('account')[0] == 'H':
                                current_sum = i.get('amount')
                                current = 'ETH'
                                tr_com = i.get('tax') * currency_eth
                                tr_sum = i.get('amount') * currency_eth
                                amount = tr_sum - tr_com
                            elif i.get('account')[0] == 'U':
                                current_sum = i.get('amount')
                                current = 'USD'
                                tr_com = i.get('tax') * currency_usd
                                tr_sum = i.get('amount') * currency_usd
                                amount = tr_sum - tr_com
                            elif i.get('account')[0] == 'T':
                                current_sum = i.get('amount')
                                current = 'USDT'
                                tr_com = i.get('tax') * currency_usd
                                tr_sum = i.get('amount') * currency_usd
                                amount = tr_sum - tr_com
                            elif i.get('account')[0] == 'E':
                                current_sum = i.get('amount')
                                current = 'EUR'
                                tr_com = i.get('tax') * currency_eur
                                tr_sum = i.get('amount') * currency_eur
                                amount = tr_sum - tr_com
                            else:
                                tr_com = i.get('tax')
                                tr_sum = i.get('amount')
                                amount = tr_sum - tr_com
                            new_data = {
                                'transaction_date': dt.fromtimestamp(int(i.get('timestamp'))),
                                'type_transaction': 'COMING',
                                'name': f'Capital_{i.get("number")}', 'description': i.get('description'),
                                'balance_holder': balance_holder[0],
                                'amount': amount, 'status': 'SUCCESSFULLY', 'author_id': 1, 'transaction_sum': tr_sum,
                                'import_id': i.get('id'), 'type_payment': type_payment, 'commission': tr_com,
                                'current_transaction': current,
                                'current_sum': current_sum, 'current_amount': i.get('amount') - i.get('tax')
                            }
                            new_transa.objects.create(**new_data)
                            old_balance_balance_holder += decimal.Decimal(amount)
                            balance_holder.update(holder_balance=old_balance_balance_holder)
                        else:
                            pass
                    else:
                        pass
            else:
                for page in range(page_count):
                    transactions_req = requests.post(
                        'https://api.capitalist.net/',
                        json={
                            "operation": "get_documents_history_ext",
                            "login": login,
                            "token": token,
                            "plain_password": password,
                            "document_state": "executed",
                            "limit": 100,
                            "page": int(page) + 1,
                            "period_from": date_start
                        },
                        headers={"x-response-format": "json"}
                    )
                    transactions = json.loads(transactions_req.content).get('data').get('history')
                    for i in transactions:
                        if len(Transaction.objects.filter(import_id=i.get('id'))) == 0:
                            old_balance_balance_holder = balance_holder[0].holder_balance
                            new_transa = Transaction
                            if i.get('outgoing') and i.get('selfExchange') is False:
                                type_payment = PayType.objects.filter(pay_type='Выплаты-партнерские')[0]
                                tr_comis = 0
                                current = None
                                current_sum = None
                                if i.get('tax'):
                                    tr_comis = i.get('tax')

                                if i.get('account')[0] == 'H':
                                    current = 'ETH'
                                    current_sum = i.get('amount')
                                    tr_comis = tr_comis * currency_eth
                                    tr_sum = i.get('amount') * currency_eth
                                    amount = tr_sum + tr_comis
                                elif i.get('account')[0] == 'U':
                                    current = 'USD'
                                    current_sum = i.get('amount')
                                    tr_comis = tr_comis * currency_usd
                                    tr_sum = i.get('amount') * currency_usd
                                    amount = tr_sum + tr_comis
                                elif i.get('account')[0] == 'T':
                                    current = 'USDT'
                                    current_sum = i.get('amount')
                                    tr_comis = tr_comis * currency_usd
                                    tr_sum = i.get('amount') * currency_usd
                                    amount = tr_sum + tr_comis
                                elif i.get('account')[0] == 'E':
                                    current = 'EUR'
                                    current_sum = i.get('amount')
                                    tr_comis = tr_comis * currency_eur
                                    tr_sum = i.get('amount') * currency_eur
                                    amount = tr_sum + tr_comis
                                else:
                                    tr_sum = i.get('amount')
                                    amount = tr_sum + tr_comis
                                new_data = {
                                    'transaction_date': dt.fromtimestamp(int(i.get('timestamp'))),
                                    'type_transaction': 'EXPENDITURE',
                                    'name': f'Capital_{i.get("number")}', 'description': i.get('description'),
                                    'balance_holder': balance_holder[0],
                                    'amount': amount, 'status': 'SUCCESSFULLY', 'author_id': 1,
                                    'transaction_sum': tr_sum,
                                    'import_id': i.get('id'), 'type_payment': type_payment, 'commission': tr_comis,
                                    'current_transaction': current,
                                    'current_sum': current_sum, 'current_amount': i.get('amount') + i.get('tax')
                                }
                                new_transa.objects.create(**new_data)
                                old_balance_balance_holder -= decimal.Decimal(amount)
                                balance_holder.update(holder_balance=old_balance_balance_holder)
                            elif i.get('outgoing') is False and i.get('selfExchange') is False:
                                type_payment = PayType.objects.filter(pay_type='Пополнение')[0]
                                current = None
                                current_sum = None
                                if i.get('account')[0] == 'H':
                                    current = 'ETH'
                                    current_sum = i.get('amount')
                                    tr_com = i.get('tax') * currency_eth
                                    tr_sum = i.get('amount') * currency_eth
                                    amount = tr_sum - tr_com
                                elif i.get('account')[0] == 'U':
                                    current = 'USD'
                                    current_sum = i.get('amount')
                                    tr_com = i.get('tax') * currency_usd
                                    tr_sum = i.get('amount') * currency_usd
                                    amount = tr_sum - tr_com
                                elif i.get('account')[0] == 'T':
                                    current = 'USDT'
                                    current_sum = i.get('amount')
                                    tr_com = i.get('tax') * currency_usd
                                    tr_sum = i.get('amount') * currency_usd
                                    amount = tr_sum - tr_com
                                elif i.get('account')[0] == 'E':
                                    current = 'EUR'
                                    current_sum = i.get('amount')
                                    tr_com = i.get('tax') * currency_eur
                                    tr_sum = i.get('amount') * currency_eur
                                    amount = tr_sum - tr_com
                                else:
                                    tr_com = i.get('tax')
                                    tr_sum = i.get('amount')
                                    amount = tr_sum - tr_com
                                new_data = {
                                    'transaction_date': dt.fromtimestamp(int(i.get('timestamp'))),
                                    'type_transaction': 'COMING',
                                    'name': f'Capital_{i.get("number")}', 'description': i.get('description'),
                                    'balance_holder': balance_holder[0],
                                    'amount': amount, 'status': 'SUCCESSFULLY', 'author_id': 1,
                                    'transaction_sum': tr_sum,
                                    'import_id': i.get('id'), 'type_payment': type_payment, 'commission': tr_com,
                                    'current_transaction': current,
                                    'current_sum': current_sum, 'current_amount': i.get('amount') - i.get('tax')
                                }
                                new_transa.objects.create(**new_data)
                                old_balance_balance_holder += decimal.Decimal(amount)
                                balance_holder.update(holder_balance=old_balance_balance_holder)
                            else:
                                pass
                        else:
                            pass
        new_start = dt.now().date() - datetime.timedelta(days=1)
        import_object = ImportData.objects.filter(bank=obj.bank)
        import_object.update(repyt_start_date=new_start)
