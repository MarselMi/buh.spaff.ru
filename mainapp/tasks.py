from __future__ import absolute_import, unicode_literals
import decimal
from spaffaccaunting.celery import app
from datetime import datetime as dt
import datetime
from mainapp.models import (
    Current, ImportData, BalanceHolder, Transaction, PayType, CurrentBalanceHolderBalance, SubPayType, CustomUser
)
import requests
import json
import time


@app.task
def import_transactions():
    objects_active = ImportData.objects.filter(status_import=True)
    system_author = int(CustomUser.objects.filter(username='ImportTransact')[0].id)
    for obj in objects_active:
        balance_holder = BalanceHolder.objects.filter(organization_holder=obj.balance_holder)

        if obj.bank.lower() == 'tinkoff':
            date_start = obj.date_start.strftime('%Y-%m-%d')
            if obj.repyt_start_date:
                date_start = obj.repyt_start_date.strftime('%Y-%m-%d')
            date_end = dt.now().date()

            transactions_objects = json.loads(requests.get(
                f"https://business.tinkoff.ru/openapi/api/v1/bank-statement?accountNumber={obj.account}&from={date_start}&till={date_end}",
                headers={'Authorization': f'Bearer {obj.key}'}
            ).content).get('operation')
            for transaction in transactions_objects:
                transaction_new = Transaction
                sub_type = None
                if len(Transaction.objects.filter(import_id=f'{obj.account}_{transaction.get("operationId")}')) == 0:
                    pay_type = PayType.objects.filter(pay_type='Временная категория')
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

                    if transaction.get('payerAccount') == obj.account:
                        type_transaction = 'EXPENDITURE'
                        import_id = f'{obj.account}_{transaction.get("operationId")}'
                        tr_name = f"{transaction.get('paymentPurpose')[:28]}..."
                        status = 'SUCCESSFULLY'
                        transaction_date = dt.strptime(transaction.get('date'), '%Y-%m-%d')
                        amount = decimal.Decimal(transaction.get('amount'))
                        description = transaction.get('paymentPurpose')

                        current = Current.objects.filter(current_name="RUR")[0]
                        current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                            current_id=current,
                            balance_holder_id=balance_holder[0]
                        )
                        old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                        old_balance_balance_holder -= decimal.Decimal(amount)
                        current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                        if sub_type:
                            new_data = {
                                'transaction_date': transaction_date, 'type_transaction': type_transaction,
                                'name': tr_name, 'description': description, 'balance_holder': balance_holder[0],
                                'amount': amount, 'status': status, 'author_id': system_author,
                                'transaction_sum': amount, 'import_id': import_id, 'type_payment': pay_type[0],
                                'sub_type_pay': sub_type[0], 'current_id': current, 'channel': transaction.get('recipient'),
                                'requisite': transaction.get('recipientAccount')
                            }
                        else:
                            new_data = {
                                'transaction_date': transaction_date, 'type_transaction': type_transaction,
                                'name': tr_name, 'description': description, 'balance_holder': balance_holder[0],
                                'amount': amount, 'status': status, 'author_id': system_author,
                                'transaction_sum': amount, 'import_id': import_id, 'type_payment': pay_type[0],
                                'current_id': current, 'channel': transaction.get('recipient'),
                                'requisite': transaction.get('recipientAccount')
                            }
                        transaction_new.objects.create(**new_data)
                    else:
                        type_transaction = 'COMING'
                        import_id = f'{obj.account}_{transaction.get("operationId")}'
                        tr_name = f"{transaction.get('paymentPurpose')[:28]}..."
                        status = 'SUCCESSFULLY'
                        transaction_date = dt.strptime(transaction.get('date'), '%Y-%m-%d')
                        amount = decimal.Decimal(transaction.get('amount'))
                        description = transaction.get('paymentPurpose')

                        current = Current.objects.filter(current_name="RUR")[0]
                        current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                            current_id=current,
                            balance_holder_id=balance_holder[0]
                        )
                        old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                        old_balance_balance_holder += decimal.Decimal(amount)
                        current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                        if sub_type:
                            new_data = {
                                'transaction_date': transaction_date, 'type_transaction': type_transaction,
                                'name': tr_name, 'description': description, 'balance_holder': balance_holder[0],
                                'amount': amount, 'status': status, 'author_id': system_author,
                                'transaction_sum': amount, 'import_id': import_id, 'type_payment': pay_type[0],
                                'sub_type_pay': sub_type[0], 'current_id': current,  'channel': transaction.get('payerName'),
                                'requisite': transaction.get('payerAccount')
                            }
                        else:
                            new_data = {
                                'transaction_date': transaction_date, 'type_transaction': type_transaction,
                                'name': tr_name, 'description': description, 'balance_holder': balance_holder[0],
                                'amount': amount, 'status': status, 'author_id': system_author,
                                'transaction_sum': amount, 'import_id': import_id, 'type_payment': pay_type[0],
                                'current_id': current, 'channel': transaction.get('payerName'),
                                'requisite': transaction.get('payerAccount')
                            }
                        transaction_new.objects.create(**new_data)

        elif obj.bank.lower() == 'capitalist':
            our_correspondent = [
                'U12650092',
                'E12650094',
                'R12650090',
                'B12650096',
                'H12650100',
                'T12650098',
                'W13217740000',
                'Y12650102',
                'I12650104',
            ]
            date_start = obj.date_start.strftime('%d.%m.%Y')
            if obj.repyt_start_date:
                date_start = obj.repyt_start_date.strftime('%d.%m.%Y')

            '''Авторизация и получение токена'''
            password = obj.key
            login = obj.account

            try:
                token_request = (requests.post(
                    'https://api.capitalist.net/',
                    json={"operation": "get_token", "login": login},
                    headers={"x-response-format": "json"})
                )

                token = json.loads(token_request.content).get('data').get('token')

                '''Запрос на историю транзакций'''
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
                '''Проверяю сколько страниц в ответе'''
                page_count = int(json.loads(transactions_history.content).get('data').get('pages').get('pageCount'))

                if page_count == 1:
                    transactions = json.loads(transactions_history.content).get('data').get('history')
                    for i in transactions:
                        if len(Transaction.objects.filter(import_id=i.get('id'))) == 0:

                            new_transa = Transaction

                            if i.get('outgoing'):
                                type_payment = PayType.objects.filter(pay_type='Выплаты-партнерские')[0]
                                if i.get('description').lower().find('conversion') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Обмен в Capitalist')[0]
                                tr_comis = i.get('tax')
                                tr_sum = i.get('amount')
                                amount = tr_sum + tr_comis
                                current = Current.objects.filter(current_name=i.get('currency'))[0]
                                current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                    current_id=current,
                                    balance_holder_id=balance_holder[0]
                                )
                                old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                old_balance_balance_holder -= decimal.Decimal(amount)
                                current_balance_holder.update(holder_current_balance=old_balance_balance_holder)
                                new_data = {
                                    'transaction_date': dt.fromtimestamp(int(i.get('timestamp'))),
                                    'type_transaction': 'EXPENDITURE', 'name': f'Capital_{i.get("number")}',
                                    'description': i.get('description'), 'balance_holder': balance_holder[0],
                                    'amount': amount, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                    'transaction_sum': tr_sum, 'import_id': i.get('id'), 'type_payment': type_payment,
                                    'commission': tr_comis, 'current_id': current, 'channel': i.get('channel'),
                                    'requisite': i.get('correspondent')
                                }
                                new_transa.objects.create(**new_data)
                            else:
                                type_payment = PayType.objects.filter(pay_type='Пополнение')[0]
                                if i.get('description').lower().find('conversion') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Обмен в Capitalist')[0]
                                tr_com = i.get('tax')
                                tr_sum = i.get('amount')
                                amount = tr_sum - tr_com
                                current = Current.objects.filter(current_name=i.get('currency'))[0]
                                current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                    current_id=current,
                                    balance_holder_id=balance_holder[0]
                                )
                                old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                old_balance_balance_holder += decimal.Decimal(amount)
                                current_balance_holder.update(holder_current_balance=old_balance_balance_holder)
                                new_data = {
                                    'transaction_date': dt.fromtimestamp(int(i.get('timestamp'))),
                                    'type_transaction': 'COMING', 'name': f'Capital_{i.get("number")}',
                                    'description': i.get('description'), 'balance_holder': balance_holder[0],
                                    'amount': amount, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                    'transaction_sum': tr_sum, 'import_id': i.get('id'), 'type_payment': type_payment,
                                    'commission': tr_com, 'current_id': current, 'channel': i.get('channel'),
                                    'requisite': i.get('correspondent')
                                }
                                new_transa.objects.create(**new_data)
                            '''Входящие внутренние транзакции'''
                            if i.get('correspondent') in our_correspondent and i.get('selfExchange'):
                                type_payment = PayType.objects.filter(pay_type='Пополнение')[0]
                                if i.get('description').lower().find('conversion') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Обмен в Capitalist')[0]
                                tr_com = i.get('tax')
                                tr_sum = amount = i.get('destAmount')
                                current = Current.objects.filter(current_name=i.get('destCurrency'))[0]
                                current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                    current_id=current,
                                    balance_holder_id=balance_holder[0]
                                )
                                old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                old_balance_balance_holder += decimal.Decimal(amount)
                                current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                                new_data = {
                                    'transaction_date': dt.fromtimestamp(int(i.get('timestamp'))),
                                    'type_transaction': 'COMING', 'name': f'Capital_{i.get("number")}',
                                    'description': i.get('description'), 'balance_holder': balance_holder[0],
                                    'amount': amount, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                    'transaction_sum': tr_sum, 'import_id': i.get('id'), 'commission': tr_com,
                                    'type_payment': type_payment, 'current_id': current, 'channel': i.get('channel'),
                                    'requisite': i.get('correspondent')
                                }
                                new_transa.objects.create(**new_data)
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

                                new_transa = Transaction

                                if i.get('outgoing'):
                                    '''Исходящие транзакции'''
                                    type_payment = PayType.objects.filter(pay_type='Выплаты-партнерские')[0]
                                    if i.get('description').lower().find('conversion') > 0:
                                        type_payment = PayType.objects.filter(pay_type='Обмен в Capitalist')[0]
                                    tr_comis = i.get('tax')
                                    tr_sum = i.get('amount')
                                    amount = tr_sum + tr_comis
                                    current = Current.objects.filter(current_name=i.get('currency'))[0]
                                    current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                        current_id=current,
                                        balance_holder_id=balance_holder[0]
                                    )
                                    old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                    old_balance_balance_holder -= decimal.Decimal(amount)
                                    current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                                    new_data = {
                                        'transaction_date': dt.fromtimestamp(int(i.get('timestamp'))),
                                        'type_transaction': 'EXPENDITURE', 'name': f'Capital_{i.get("number")}',
                                        'description': i.get('description'), 'balance_holder': balance_holder[0],
                                        'amount': amount, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                        'transaction_sum': tr_sum, 'import_id': i.get('id'), 'commission': tr_comis,
                                        'type_payment': type_payment, 'current_id': current, 'channel': i.get('channel'),
                                        'requisite': i.get('correspondent')
                                    }
                                    new_transa.objects.create(**new_data)
                                else:
                                    '''Входящие транзакции'''
                                    type_payment = PayType.objects.filter(pay_type='Пополнение')[0]
                                    if i.get('description').lower().find('conversion') > 0:
                                        type_payment = PayType.objects.filter(pay_type='Обмен в Capitalist')[0]
                                    tr_com = i.get('tax')
                                    tr_sum = i.get('amount')
                                    amount = tr_sum - tr_com
                                    current = Current.objects.filter(current_name=i.get('currency'))[0]
                                    current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                        current_id=current,
                                        balance_holder_id=balance_holder[0]
                                    )
                                    old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                    old_balance_balance_holder += decimal.Decimal(amount)
                                    current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                                    new_data = {
                                        'transaction_date': dt.fromtimestamp(int(i.get('timestamp'))),
                                        'type_transaction': 'COMING', 'name': f'Capital_{i.get("number")}',
                                        'description': i.get('description'), 'balance_holder': balance_holder[0],
                                        'amount': amount, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                        'transaction_sum': tr_sum, 'import_id': i.get('id'), 'commission': tr_com,
                                        'type_payment': type_payment, 'current_id': current, 'channel': i.get('channel'),
                                        'requisite': i.get('correspondent')
                                    }
                                    new_transa.objects.create(**new_data)
                                if i.get('correspondent') in our_correspondent and i.get('selfExchange'):
                                    '''Входящие внутренние транзакции'''
                                    type_payment = PayType.objects.filter(pay_type='Пополнение')[0]
                                    if i.get('description').lower().find('conversion') > 0:
                                        type_payment = PayType.objects.filter(pay_type='Обмен в Capitalist')[0]
                                    tr_com = i.get('tax')
                                    tr_sum = amount = i.get('destAmount')
                                    current = Current.objects.filter(current_name=i.get('destCurrency'))[0]
                                    current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                        current_id=current,
                                        balance_holder_id=balance_holder[0]
                                    )
                                    old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                    old_balance_balance_holder += decimal.Decimal(amount)
                                    current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                                    new_data = {
                                        'transaction_date': dt.fromtimestamp(int(i.get('timestamp'))),
                                        'type_transaction': 'COMING', 'name': f'Capital_{i.get("number")}',
                                        'description': i.get('description'), 'balance_holder': balance_holder[0],
                                        'amount': amount, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                        'transaction_sum': tr_sum, 'import_id': i.get('id'), 'commission': tr_com,
                                        'type_payment': type_payment, 'current_id': current, 'channel': i.get('channel'),
                                        'requisite': i.get('correspondent')
                                    }
                                    new_transa.objects.create(**new_data)
            except:
                pass

        elif obj.bank.lower() == 'modulbank':
            date_start = obj.date_start.strftime('%Y-%m-%dT00:00:00')+"Z"
            if obj.repyt_start_date:
                date_start = obj.repyt_start_date.strftime('%Y-%m-%dT00:00:00')+"Z"
            date_end = dt.now().date().strftime('%Y-%m-%dT00:00:00')+"Z"
            try:
                accounts_modulbank = json.loads(requests.post(
                    f"https://api.modulbank.ru/v1/account-info/",
                    headers={'Authorization': f'Bearer {obj.key}'}
                ).content)[0].get('bankAccounts')
                corr_account_id = list(filter(lambda a: a.get('number') == obj.account, accounts_modulbank))[0].get('id')
                skip_count = 0

                transactions_history = json.loads(requests.post(
                    f"https://api.modulbank.ru/v1/operation-history/{corr_account_id}",
                    headers={'Authorization': f'Bearer {obj.key}'},
                    data={
                        "statuses": [
                            "Executed", "Received", "PayReceived"
                            ],
                        "from": date_start,
                        "till": date_end,
                        "skip": skip_count,
                        "records": 50
                    }
                ).content)
                transaction_new = Transaction

                if len(transactions_history) < 50:
                    for transaction in transactions_history:
                        if Transaction.objects.filter(import_id=transaction.get("id")).exists() is False:
                            if transaction.get('category') == "Credit":
                                sub_type = None
                                description = transaction.get('paymentPurpose')

                                if description.lower().find('реклам') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Реклама')[0]
                                elif description.lower().find('комиссия за') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Услуги Банка')[0]
                                    sub_type = SubPayType.objects.filter(sub_type='Комиссия')[0]
                                elif description.lower().find('по для эвм') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Использование ПО для ЭВМ')[0]
                                elif description.lower().find('интернет-услуги') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Интернет')[0]
                                elif description.lower().find('разраб') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Услуги по разработке')[0]
                                elif description.lower().find('привлечение пользователей') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Выплаты-партнерские')[0]
                                else:
                                    type_payment = PayType.objects.filter(pay_type='Прочие')[0]

                                tr_com = 0
                                tr_current = 'RUR'
                                tr_sum = decimal.Decimal(transaction.get('amount'))

                                tr_datetime = dt.strptime(transaction.get('executed'), '%Y-%m-%dT%H:%M:%S')
                                amount = tr_sum + tr_com
                                current = Current.objects.filter(current_name=tr_current)[0]
                                current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                    current_id=current,
                                    balance_holder_id=balance_holder[0]
                                )
                                old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                old_balance_balance_holder -= decimal.Decimal(amount)
                                current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                                new_data = {
                                    'transaction_date': tr_datetime, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                    'type_transaction': 'EXPENDITURE', 'current_id': current, 'sub_type_pay': sub_type,
                                    'description': description, 'balance_holder': balance_holder[0],
                                    'amount': amount, 'transaction_sum': tr_sum, 'import_id': transaction.get('id'),
                                    'commission': tr_com, 'name': f'ModulBank_{transaction.get("id")[:8]}',
                                    'type_payment': type_payment, 'channel': transaction.get('contragentName'),
                                    'requisite': transaction.get('contragentBankAccountNumber')
                                }
                                transaction_new.objects.create(**new_data)
                            else:
                                type_payment = PayType.objects.filter(pay_type='Пополнение')[0]
                                description = transaction.get('paymentPurpose')

                                tr_com = 0
                                tr_current = 'RUR'
                                tr_sum = decimal.Decimal(transaction.get('amount'))

                                tr_datetime = dt.strptime(transaction.get('executed'), '%Y-%m-%dT%H:%M:%S')
                                amount = tr_sum + tr_com
                                current = Current.objects.filter(current_name=tr_current)[0]
                                current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                    current_id=current,
                                    balance_holder_id=balance_holder[0]
                                )
                                old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                old_balance_balance_holder += decimal.Decimal(amount)
                                current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                                new_data = {
                                    'transaction_date': tr_datetime, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                    'type_transaction': 'COMING', 'current_id': current, 'description': description,
                                    'balance_holder': balance_holder[0], 'amount': amount, 'transaction_sum': tr_sum,
                                    'import_id': transaction.get('id'), 'type_payment': type_payment,
                                    'commission': tr_com, 'name': f'ModulBank_{transaction.get("id")[:8]}',
                                    'channel': transaction.get('contragentName'),
                                    'requisite': transaction.get('contragentBankAccountNumber')
                                }
                                transaction_new.objects.create(**new_data)
                else:
                    while len(transactions_history) == 50:
                        for transaction in transactions_history:
                            if Transaction.objects.filter(import_id=transaction.get("id")).exists() is False:
                                if transaction.get('category') == "Credit":
                                    sub_type = None
                                    description = transaction.get('paymentPurpose')

                                    if description.lower().find('реклам') > 0:
                                        type_payment = PayType.objects.filter(pay_type='Реклама')[0]
                                    elif description.lower().find('комиссия за') > 0:
                                        type_payment = PayType.objects.filter(pay_type='Услуги Банка')[0]
                                        sub_type = SubPayType.objects.filter(sub_type='Комиссия')[0]
                                    elif description.lower().find('по для эвм') > 0:
                                        type_payment = PayType.objects.filter(pay_type='Использование ПО для ЭВМ')[0]
                                    elif description.lower().find('интернет-услуги') > 0:
                                        type_payment = PayType.objects.filter(pay_type='Интернет')[0]
                                    elif description.lower().find('разраб') > 0:
                                        type_payment = PayType.objects.filter(pay_type='Услуги по разработке')[0]
                                    elif description.lower().find('привлечение пользователей') > 0:
                                        type_payment = PayType.objects.filter(pay_type='Выплаты-партнерские')[0]
                                    else:
                                        type_payment = PayType.objects.filter(pay_type='Прочие')[0]

                                    tr_com = 0
                                    tr_current = 'RUR'
                                    tr_sum = decimal.Decimal(transaction.get('amount'))

                                    tr_datetime = dt.strptime(transaction.get('executed'), '%Y-%m-%dT%H:%M:%S')
                                    amount = tr_sum + tr_com
                                    current = Current.objects.filter(current_name=tr_current)[0]
                                    current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                        current_id=current,
                                        balance_holder_id=balance_holder[0]
                                    )
                                    old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                    old_balance_balance_holder -= decimal.Decimal(amount)
                                    current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                                    new_data = {
                                        'transaction_date': tr_datetime, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                        'type_transaction': 'EXPENDITURE', 'current_id': current, 'sub_type_pay': sub_type,
                                        'description': description, 'balance_holder': balance_holder[0],
                                        'amount': amount, 'transaction_sum': tr_sum, 'import_id': transaction.get('id'),
                                        'commission': tr_com, 'name': f'ModulBank_{transaction.get("companyId")[:8]}',
                                        'type_payment': type_payment, 'channel': transaction.get('contragentName'),
                                        'requisite': transaction.get('contragentBankAccountNumber')
                                    }
                                    transaction_new.objects.create(**new_data)
                                else:
                                    type_payment = PayType.objects.filter(pay_type='Пополнение')[0]
                                    description = transaction.get('paymentPurpose')

                                    tr_com = 0
                                    tr_current = 'RUR'
                                    tr_sum = decimal.Decimal(transaction.get('amount'))

                                    tr_datetime = dt.strptime(transaction.get('executed'), '%Y-%m-%dT%H:%M:%S')
                                    amount = tr_sum + tr_com
                                    current = Current.objects.filter(current_name=tr_current)[0]
                                    current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                        current_id=current,
                                        balance_holder_id=balance_holder[0]
                                    )
                                    old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                    old_balance_balance_holder += decimal.Decimal(amount)
                                    current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                                    new_data = {
                                        'transaction_date': tr_datetime, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                        'type_transaction': 'COMING', 'current_id': current, 'description': description,
                                        'balance_holder': balance_holder[0], 'amount': amount, 'transaction_sum': tr_sum,
                                        'import_id': transaction.get('id'), 'type_payment': type_payment,
                                        'commission': tr_com, 'name': f'ModulBank_{transaction.get("companyId")[:8]}',
                                        'channel': transaction.get('contragentName'),
                                        'requisite': transaction.get('contragentBankAccountNumber')
                                    }
                                    transaction_new.objects.create(**new_data)

                        skip_count += 50
                        time.sleep(1)

                        transactions_history = json.loads(requests.post(
                            f"https://api.modulbank.ru/v1/operation-history/{corr_account_id}/",
                            headers={'Authorization': f'Bearer {obj.key}'},
                            data={
                                "statuses": [
                                    "Executed", "Received", "PayReceived"
                                ],
                                "from": date_start,
                                "till": date_end,
                                "skip": skip_count,
                                "records": 50
                            }
                        ).content)

                    for transaction in transactions_history:
                        if Transaction.objects.filter(import_id=transaction.get("id")).exists() is False:
                            if transaction.get('category') == "Credit":
                                sub_type = None
                                description = transaction.get('paymentPurpose')

                                if description.lower().find('реклам') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Реклама')[0]
                                elif description.lower().find('комиссия за') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Услуги Банка')[0]
                                    sub_type = SubPayType.objects.filter(sub_type='Комиссия')[0]
                                elif description.lower().find('по для эвм') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Использование ПО для ЭВМ')[0]
                                elif description.lower().find('интернет-услуги') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Интернет')[0]
                                elif description.lower().find('разраб') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Услуги по разработке')[0]
                                elif description.lower().find('привлечение пользователей') > 0:
                                    type_payment = PayType.objects.filter(pay_type='Выплаты-партнерские')[0]
                                else:
                                    type_payment = PayType.objects.filter(pay_type='Прочие')[0]

                                tr_com = 0
                                tr_current = 'RUR'
                                tr_sum = decimal.Decimal(transaction.get('amount'))

                                tr_datetime = dt.strptime(transaction.get('executed'), '%Y-%m-%dT%H:%M:%S')
                                amount = tr_sum + tr_com
                                current = Current.objects.filter(current_name=tr_current)[0]
                                current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                    current_id=current,
                                    balance_holder_id=balance_holder[0]
                                )
                                old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                old_balance_balance_holder -= decimal.Decimal(amount)
                                current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                                new_data = {
                                    'transaction_date': tr_datetime, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                    'type_transaction': 'EXPENDITURE', 'current_id': current, 'sub_type_pay': sub_type,
                                    'description': description, 'balance_holder': balance_holder[0],
                                    'amount': amount, 'transaction_sum': tr_sum, 'import_id': transaction.get('id'),
                                    'commission': tr_com, 'name': f'ModulBank_{transaction.get("id")[:8]}',
                                    'type_payment': type_payment, 'channel': transaction.get('contragentName'),
                                    'requisite': transaction.get('contragentBankAccountNumber')
                                }
                                transaction_new.objects.create(**new_data)
                            else:
                                type_payment = PayType.objects.filter(pay_type='Пополнение')[0]
                                description = transaction.get('paymentPurpose')

                                tr_com = 0
                                tr_current = 'RUR'
                                tr_sum = decimal.Decimal(transaction.get('amount'))

                                tr_datetime = dt.strptime(transaction.get('executed'), '%Y-%m-%dT%H:%M:%S')
                                amount = tr_sum + tr_com
                                current = Current.objects.filter(current_name=tr_current)[0]
                                current_balance_holder = CurrentBalanceHolderBalance.objects.filter(
                                    current_id=current,
                                    balance_holder_id=balance_holder[0]
                                )
                                old_balance_balance_holder = current_balance_holder[0].holder_current_balance
                                old_balance_balance_holder += decimal.Decimal(amount)
                                current_balance_holder.update(holder_current_balance=old_balance_balance_holder)

                                new_data = {
                                    'transaction_date': tr_datetime, 'status': 'SUCCESSFULLY', 'author_id': system_author,
                                    'type_transaction': 'COMING', 'current_id': current, 'description': description,
                                    'balance_holder': balance_holder[0], 'amount': amount, 'transaction_sum': tr_sum,
                                    'import_id': transaction.get('id'), 'type_payment': type_payment,
                                    'commission': tr_com, 'name': f'ModulBank_{transaction.get("id")[:8]}',
                                    'channel': transaction.get('contragentName'),
                                    'requisite': transaction.get('contragentBankAccountNumber')
                                }
                                transaction_new.objects.create(**new_data)
            except:
                pass

        new_start = dt.now().date() - datetime.timedelta(days=1)
        import_object = ImportData.objects.filter(bank=obj.bank)
        import_object.update(repyt_start_date=new_start)
