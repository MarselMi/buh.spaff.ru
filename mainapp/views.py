import json
import decimal
import math
from hashlib import md5
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from datetime import datetime as dt
from mainapp.data_library import *
from mainapp.forms import (
    TransactionForm, BalanceHolderForm, TransactionUpdateForm
)
from mainapp.models import (
    CustomUser, Transaction, BalanceHolder, PayType, ImportData,
    AdditionalDataTransaction, TransactionLog, SubPayType, BdrFond
)


def transactions_import(request):

    if request.user.is_superuser:
        balance_holders = get_allow_and_hide_balance_holders(request.user.id, simple_user=False)
    else:
        balance_holders = get_allow_and_hide_balance_holders(request.user.id, simple_user=True)
    available_holders = []

    for i in balance_holders:
        available_holders.append(i.get('organization_holder'))

    import_all_data = ImportData.objects.all()
    import_data = []
    for i in import_all_data:
        if str(i.balance_holder) in available_holders:
            import_data.append(i)

    if request.method == 'POST':

        if request.POST.get('type') == 'status_import':
            import_data = ImportData.objects.filter(pk=request.POST.get('import_id'))
            if request.POST.get('stat') == 'false':
                new_stat = False
            else:
                new_stat = True
            import_data.update(status_import=new_stat)
            bal_hol = str(import_data[0].balance_holder)
            return JsonResponse({'holder': bal_hol})

        if request.POST.get('type') == 'check_holder':
            organization_holder = request.POST.get('balance_holder')
            if BalanceHolder.objects.filter(organization_holder=organization_holder).exists():
                return JsonResponse({'message': True})
            else:
                return JsonResponse({'message': False})

        bank = request.POST.get('bank_type')
        key = request.POST.get('key')
        account = request.POST.get('account')
        inn = request.POST.get('inn')
        date_start = dt.strptime(request.POST.get('date_start'), '%d.%m.%Y').date()
        balance_holder = BalanceHolder.objects.filter(organization_holder=request.POST.get('balance_holder'))[0]
        status_import = True

        new_import = ImportData

        new_data = {
            'bank': bank,
            'key': key,
            'account': account,
            'inn': inn,
            'date_start': date_start,
            'balance_holder': balance_holder,
            'status_import': status_import,
            'author': request.user.id
        }

        new_import.objects.create(**new_data)

    data = {'title': 'Иморт данных', 'balance_holders': balance_holders, 'import_data': import_data}
    return render(request, 'mainapp/transactions_import.html', data)


def fond_view(request):

    pdr_fond_show = None

    if request.method == 'POST':

        if request.POST.get('balance_holder'):
            '''для создания БДР'''
            bal_hold = BalanceHolder.objects.filter(organization_holder=request.POST.get('balance_holder'))[0]
            month = request.POST.get('month')
            year = request.POST.get('year')
            dates = dt.strptime(f'{month}-{year}', '%d-%m-%Y').date()

            new_dict = {
                'balance_holder_id': '',
                'month_year': '',
                'params_data': {}
            }

            didi = dict(request.POST)
            del didi['csrfmiddlewaretoken']
            del didi['month']
            del didi['year']
            del didi['balance_holder']

            for i in didi:
                if (i.find('pay_type')) == 0:
                    new_dict['params_data'].setdefault(i,
                                                       {
                                                           'value': didi[i][0],
                                                           'type_id': (i.split('&'))[1],
                                                           'html_el_id': f"{(i.split('&'))[0]}_{(i.split('&'))[1]}_{(i.split('&'))[-1]}",
                                                           'label': (i.split('&'))[2],
                                                           'type': (i.split('&'))[-1]
                                                       }
                                                       )
                elif (i.find('pay_sub_type')) == 0:
                    new_dict['params_data'].setdefault(i,
                                                       {
                                                           'value': didi[i][0],
                                                           'sub_id': (i.split('&'))[1],
                                                           'html_el_id': f"{(i.split('&'))[0]}_{(i.split('&'))[1]}_{(i.split('&'))[-1]}",
                                                           'label': (i.split('&'))[2],
                                                           'type': (i.split('&'))[-1]
                                                       }
                                                       )

            new_dict['balance_holder_id'] = bal_hold
            new_dict['month_year'] = dates
            json.dumps(new_dict['params_data'])
            new_bdr = BdrFond
            new_bdr.objects.create(**new_dict)

        if request.POST.get('type') == 'show_bdr':
            bal_req = request.POST.get('balance_holder_req')
            bal_req_id = BalanceHolder.objects.filter(organization_holder=bal_req)[0].pk
            req_start_date = f"01-{request.POST.get('start_bdr')}"
            start_date = dt.strptime(req_start_date, '%d-%m-%Y')

            if request.POST.get('end_bdr'):
                date_replace = request.POST.get('end_bdr').split('-')
                if date_replace[0] != '12':
                    date_replace = f'{1 + int(date_replace[0])}-{date_replace[1]}'
                else:
                    date_replace = f'01-{1 + int(date_replace[1])}'
                req_end_date = dt.strptime(f"01-{date_replace}", '%d-%m-%Y')
            else:
                req_end_date = start_date

            bdr_fond_show = get_bdr_data(balance_holder=bal_req_id, start=start_date, end=req_end_date)

            filters_transaction = {'start': start_date, 'end': req_end_date, 'balance_holder_id': bal_req_id}
            fact_transactions = get_for_bdr_transaction(filter_data=filters_transaction)

            data_tr_fact_elementary = {
                'доход': {},
                'расход': {}
            }
            data_for_table = {
                'доход': {},
                'расход': {}
            }
            data_tr_ready = {
                'доход': {},
                'расход': {}
            }
            all_data_plane_fact = {
                'расход': {},
                'доход': {},
                'diff': {}
            }

            '''Все фактические транзакции'''
            for tr in fact_transactions:
                for key, val in tr.items():
                    if val == 'COMING':
                        if tr.get('sub_type_pay_id'):
                            type_sub = f"{tr.get('type_payment')}_{tr.get('sub_type_pay_id')}"
                        else:
                            type_sub = tr.get('type_payment')

                        if data_tr_fact_elementary['доход'].get(type_sub):
                            data_tr_fact_elementary['доход'][type_sub] += tr.get('amount')
                        else:
                            data_tr_fact_elementary['доход'].setdefault(type_sub, tr.get('amount'))
                    elif val == 'EXPENDITURE':
                        if tr.get('sub_type_pay_id'):
                            type_sub = f"{tr.get('type_payment')}_{tr.get('sub_type_pay_id')}"
                        else:
                            type_sub = tr.get('type_payment')

                        if data_tr_fact_elementary['расход'].get(type_sub):
                            data_tr_fact_elementary['расход'][type_sub] += tr.get('amount')
                        else:
                            data_tr_fact_elementary['расход'].setdefault(type_sub, tr.get('amount'))

            '''Параметры по запланированным данным'''
            for i in bdr_fond_show:
                di_encode = json.loads(i.get('params_data'))
                for key, val in di_encode.items():
                    if key.find('expend') > 0:
                        data_for_table['расход'].setdefault(val.get('label'), int())
                        data_for_table['расход'][val.get('label')] += int(val.get('value'))
                    else:
                        data_for_table['доход'].setdefault(val.get('label'), int())
                        data_for_table['доход'][val.get('label')] += int(val.get('value'))

            for va, kr in data_for_table.items():
                fact_finaly = 0
                plane_finaly = 0
                for key, val in data_for_table.get(va).items():
                    plane_finaly += data_for_table.get(va).get(key)
                    if data_tr_fact_elementary.get(va).get(key):
                        fact_finaly += data_tr_fact_elementary.get(va).get(key)
                        data_tr_ready[va].setdefault(key, data_tr_fact_elementary.get(va).get(key))
                    else:
                        data_tr_ready[va].setdefault(key, 0)
                data_tr_ready[va].setdefault('final', fact_finaly)
                data_for_table[va].setdefault('final', plane_finaly)

            def proc(first, second):
                if second == 0:
                    return 100
                else:
                    return round(first / second * 100, 2)

            for i, k in data_for_table.items():
                if i == 'доход':
                    for key, val in k.items():
                        all_data_plane_fact['доход'].setdefault(key, {'plan': val, 'fact': data_tr_ready['доход'].get(key),
                                                        'raznica': data_tr_ready['доход'].get(key) - val,
                                                        'proc': proc(data_tr_ready['доход'].get(key) - val, val)})
                elif i == 'расход':
                    for key, val in k.items():
                        all_data_plane_fact['расход'].setdefault(key, {'plan': val, 'fact': data_tr_ready['расход'].get(key),
                                                         'raznica': val - data_tr_ready['расход'].get(key),
                                                         'proc': proc(val - data_tr_ready['расход'].get(key), val)})

            all_data_plane_fact['diff'].setdefault('plan',
                all_data_plane_fact['доход']['final'].get('plan') - all_data_plane_fact['расход']['final'].get('plan')
            )

            all_data_plane_fact['diff'].setdefault('fact',
                all_data_plane_fact['доход']['final'].get('fact') - all_data_plane_fact['расход']['final'].get('fact')
            )

            all_data_plane_fact['diff'].setdefault('raznica',
                all_data_plane_fact['diff'].get('fact') - all_data_plane_fact['diff'].get('plan')
            )

            return JsonResponse({'res': all_data_plane_fact})

        if request.POST.get('type') == 'balance_holder':
            try:
                bal_holder = BalanceHolder.objects.filter(organization_holder=request.POST.get('bal_holder'))[0].pk
                bdr_info = BdrFond.objects.filter(balance_holder_id=bal_holder).last()

                year = dt.strftime(bdr_info.month_year, '%Y')
                month = dt.strftime(bdr_info.month_year, '%d-%m')
                if int(month.split('-')[1]) != 12:
                    if int(month.split('-')[1]) < 10:
                        month = f"01-0{1 + int(month.split('-')[1])}"
                    else:
                        month = f"01-{1 + int(month.split('-')[1])}"
                else:
                    month = '01-01'
                    year = int(year) + 1
                data_output = bdr_info.params_data
                list_data = []
                for i in data_output:
                    list_data.append([i, data_output[i]])
                return JsonResponse({'bal_holder': list_data, 'date_year': year, 'date_month': month})
            except:
                bdr_info = []
                return JsonResponse({'bal_holder': bdr_info})

        if request.POST.get('type') == 'bal_hol_req_sql':
            bal_hol = BalanceHolder.objects.filter(organization_holder=request.POST.get('bal_holder'))[0].pk
            allow_dates = get_bdr_data_holders(balance_holder_dates=bal_hol)
            for date in allow_dates:
                date['month_year'] = dt.strftime(date.get('month_year'), '%m-%Y')
            return JsonResponse({'allow_date': allow_dates})

    bdr_fond_information_for_show = get_bdr_bal_holders()
    month_dict = {
        '01-01': 'Январь',
        '01-02': 'Февраль',
        '01-03': 'Март',
        '01-04': 'Апрель',
        '01-05': 'Май',
        '01-06': 'Июнь',
        '01-07': 'Июль',
        '01-08': 'Август',
        '01-09': 'Сентябрь',
        '01-10': 'Октябрь',
        '01-11': 'Ноябрь',
        '01-12': 'Декабрь'
    }

    balance_holders = []

    if request.user.is_superuser:
        balance_holders = get_allow_and_hide_balance_holders(request.user.id, simple_user=False)
    else:
        balance_holders = get_allow_and_hide_balance_holders(request.user.id, simple_user=True)

    type_pay = PayType.objects.all()

    type_pay_for_final = []
    for i in type_pay:
        if i.subtypes_of_the_type.all():
            for sub in i.subtypes_of_the_type.all():
                type_pay_for_final.append({'sub_id': f'{i.id}_{sub.id}', 'sub_type': f'{i.pay_type}_{sub.sub_type}'})
        else:
            type_pay_for_final.append({'type_id': i.id, 'pay_type': i.pay_type})

    year_list = [dt.now().year - 1, dt.now().year, dt.now().year + 1, dt.now().year + 2]

    data = {'title': 'Фонд', 'month_dict': month_dict, 'pdr_fond_show': pdr_fond_show,
            'balance_holders': balance_holders, 'type_pay': type_pay, 'type_pay_for_final': type_pay_for_final,
            'bdr_fond_information': bdr_fond_information_for_show, 'year_list': year_list}

    return render(request, 'mainapp/fond.html', data)


def main_page_view(request):
    holders = []
    comming_sum = ''
    expenditure_sum = ''
    all_coming = 0
    all_expenditure = 0
    if request.user.is_superuser:
        holders = get_allow_balance_holders(request.user.id, simple_user=False)
        comming_sum = get_all_coming_transactions_sum(request.user.id, simpleuser=False)
        expenditure_sum = get_all_expenditure_transactions_sum(request.user.id, simpleuser=False)
    else:
        holders = get_allow_balance_holders(request.user.id, simple_user=True)
        comming_sum = get_all_coming_transactions_sum(request.user.id, simpleuser=True)
        expenditure_sum = get_all_expenditure_transactions_sum(request.user.id, simpleuser=True)

    type_payments = PayType.objects.all()
    try:
        for k in comming_sum:
            all_coming += k.get('coming')
    except:
        pass
    try:
        for k in expenditure_sum:
            all_expenditure += k.get('expenditure')
    except:
        pass

    if request.method == 'POST':

        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                pay_type_element = PayType.objects.filter(pay_type=pay_type)[0].subtypes_of_the_type.all()
                sub_type_pay = []
                for i in pay_type_element:
                    sub_type_pay.append(i.sub_type)
                return JsonResponse({'message': sub_type_pay})
            else:
                return JsonResponse({'message': False})

        if request.POST.get('type') == 'create_transaction':

            holder = BalanceHolder.objects.filter(organization_holder=request.POST.get('holder_post'))[0]

            transaction_name = request.POST.get('transaction_name_post')
            transaction_date = dt.strptime(request.POST.get('transaction_date_post'), '%d.%m.%Y').date()
            payment_type = PayType.objects.filter(pay_type=request.POST.get('payment_type_post'))[0]
            sub_type = None
            if request.POST.get('sub_type'):
                sub_type = SubPayType.objects.filter(sub_type=request.POST.get('sub_type'))[0]

            commission = 0
            if request.POST.get('commission_post'):
                commission = decimal.Decimal(request.POST.get('commission_post').replace(',', '.').replace(' ', ''))
            transaction_sum = decimal.Decimal(request.POST.get('transaction_sum_post').replace(',', '.').replace(' ', ''))
            amount = transaction_sum + commission

            transaction_type = request.POST.get('transaction_type_post')

            if transaction_type == 'Приход':
                transaction_type = 'COMING'
            else:
                transaction_type = 'EXPENDITURE'

            author_id = request.user.id

            '''Логика для загрузки ЧЕКов'''
            image = request.FILES.get('check_img_post')
            if image:
                check_img = f"img/{str(image).replace(' ', '_')}"
                root = f'{settings.MEDIA_ROOT}/{str(check_img)}'
                with open(root, 'wb+') as f:
                    for chunk in image.chunks():
                        f.write(chunk)
                image = check_img

            create_transaction = {
                'sub_type_pay': sub_type,
                'type_transaction': transaction_type,
                'transaction_date': transaction_date,
                'name': transaction_name,
                'balance_holder': holder,
                'commission': commission,
                'transaction_sum': transaction_sum,
                'amount': amount,
                'type_payment': payment_type,
                'check_img': image,
                'author_id': author_id
            }

            transaction = Transaction

            transaction.objects.create(**create_transaction)

            balance_holder_response = BalanceHolder.objects.filter(organization_holder=holder)
            old_balance_balance_holder = balance_holder_response[0].holder_balance
            if transaction_type == 'COMING':
                old_balance_balance_holder += amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
            else:
                old_balance_balance_holder -= amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)

            return HttpResponse(json.dumps({"Status": "OK"}))

        if request.POST.get('type') == 'holder':
            holder_id = request.POST.get('id')
            holder_transaction_coming = get_all_coming_transactions_sum(request.user.id, holder=holder_id)
            holder_transaction_expenditure = get_all_expenditure_transactions_sum(request.user.id, holder=holder_id)

            holder_label_expenditure = []
            holder_profit_expenditure = []
            holder_label_coming = []
            holder_profit_coming = []

            for i in holder_transaction_coming:
                holder_label_coming.append(i['type'])
                holder_profit_coming.append(float(i['coming']))

            for i in holder_transaction_expenditure:
                holder_label_expenditure.append(i['type'])
                holder_profit_expenditure.append(float(i['expenditure']))

            data = {
                'holder_label_expenditure': holder_label_expenditure,
                'holder_profit_expenditure': holder_profit_expenditure,
                'holder_label_coming': holder_label_coming,
                'holder_profit_coming': holder_profit_coming
            }

            return HttpResponse(json.dumps(data))

    label_coming = []
    profit_coming = []
    for i in comming_sum:
        label_coming.append(i['type'])
        profit_coming.append(float(i['coming']))

    label_expenditure = []
    profit_expenditure = []
    for i in expenditure_sum:
        label_expenditure.append(i['type'])
        profit_expenditure.append(float(i['expenditure']))

    data = {'title': 'Главная страница', 'holders': holders,
            'type_payments': type_payments, 'comming_sum': comming_sum, 'expenditure_sum': expenditure_sum,
            'label_coming': label_coming, 'profit_coming': profit_coming, 'profit_expenditure': profit_expenditure,
            'label_expenditure': label_expenditure, 'all_coming': all_coming, 'all_expenditure': all_expenditure
            }

    return render(request, 'mainapp/main-page.html', data)


def transaction_view(request):
    balance_holders = []
    transactions = []
    authors = CustomUser.objects.all()
    type_payments = PayType.objects.all()
    sub_type = SubPayType.objects.all()
    dict_for_sql_filter = dict()
    get_param_filter = dict(request.GET)

    collapsed = request.session.get('transaction_collapse')
    if collapsed is None:
        request.session['transaction_collapse'] = 2

    limit = request.session.get("limit_transactions")
    if not limit:
        request.session["limit_transactions"] = 25
    try:
        page = int(request.GET.get('page'))
    except:
        page = None
    if not page:
        page = 1

    if request.method == "POST":
        '''Для установки лимита вывода информации'''
        if request.POST.get('type') == 'limit25':
            request.session["limit_transactions"] = 25
            return HttpResponse({'status': 'OK'})
        if request.POST.get('type') == 'limit50':
            request.session["limit_transactions"] = 50
            return HttpResponse({'status': 'OK'})
        if request.POST.get('type') == 'limit100':
            request.session["limit_transactions"] = 100
            return HttpResponse({'status': 'OK'})

    limit = request.session["limit_transactions"]
    if page == 1:
        offset = None
    elif page == 2:
        offset = limit
    else:
        offset = limit * (page - 1)
    request.session['offset_transactions'] = offset
    ''' Заполенние словаря для SQL-запроса '''
    for element in get_param_filter:
        if element != 'page':
            if get_param_filter.get(element) != [''] and element != 'collapse' and element != 'csrfmiddlewaretoken':
                dict_for_sql_filter.setdefault(element, get_param_filter[element][0])

    '''Заменяю данные для отработки SQL запроса '''
    if dict_for_sql_filter.get('type_payment_id'):
        dict_for_sql_filter['type_payment_id'] = type_payments.filter(pay_type=dict_for_sql_filter.get('type_payment_id')).values('id')[0].get('id')

    if dict_for_sql_filter.get('sub_type_pay_id'):
        dict_for_sql_filter['sub_type_pay_id'] = sub_type.filter(sub_type=dict_for_sql_filter.get('sub_type_pay_id')).values('id')[0].get('id')

    if dict_for_sql_filter.get('author_id'):
        dict_for_sql_filter['author_id'] = authors.filter(username=dict_for_sql_filter.get('author_id')).values('id')[0].get('id')

    if dict_for_sql_filter.get('balance_holder_id'):
        dict_for_sql_filter['balance_holder_id'] = BalanceHolder.objects.filter(organization_holder=dict_for_sql_filter.get('balance_holder_id')).values('id')[0].get('id')

    if dict_for_sql_filter.get('amount_start'):
        dict_for_sql_filter['amount_start'] = dict_for_sql_filter.get('amount_start').replace(' ', '').replace(',', '.')

    if dict_for_sql_filter.get('amount_end'):
        dict_for_sql_filter['amount_end'] = dict_for_sql_filter.get('amount_end').replace(' ', '').replace(',', '.')

    if dict_for_sql_filter.get('start'):
        dict_for_sql_filter['start'] = dt.strptime(dict_for_sql_filter.get('start'), '%d.%m.%Y').strftime('%Y-%m-%d')

    if dict_for_sql_filter.get('end'):
        dict_for_sql_filter['end'] = dt.strptime(dict_for_sql_filter.get('end'), '%d.%m.%Y').strftime('%Y-%m-%d')

    if request.user.is_superuser:
        balance_holders = get_allow_balance_holders(request.user.id, simple_user=False)
        transactions = get_allow_transaction_filter(request.user.id, filter_data=dict_for_sql_filter, limit=limit, offset=offset)
        original_count = get_count_allow_transaction_filter(request.user.id, filter_data=dict_for_sql_filter)[0].get('COUNT(`mt`.`id`)')
    else:
        balance_holders = get_allow_balance_holders(request.user.id, simple_user=True)
        transactions = get_allow_transaction_filter(request.user.id, filter_data=dict_for_sql_filter, author_res=True, limit=limit, offset=offset)
        original_count = get_count_allow_transaction_filter(request.user.id, filter_data=dict_for_sql_filter, author_res=True)[0].get('COUNT(`mt`.`id`)')

    coming_sum = 0
    expenditure_comission = 0
    expenditure_transaction = 0
    expenditure_amount = 0
    for transaction in transactions:
        if transaction.get('type_transaction') == 'COMING':
            coming_sum += round(float(transaction.get('amount')), 2)
        if transaction.get('type_transaction') == 'EXPENDITURE':
            expenditure_amount += round(float(transaction.get('amount')), 2)
            expenditure_comission += round(float(transaction.get('commission')), 2)
            expenditure_transaction += round(float(transaction.get('transaction_sum')), 2)
        if transaction.get('commission'):
            transaction['percent'] = round((float(transaction.get('commission')) / float(transaction.get('transaction_sum')) * 100), 2)
    count = math.ceil(int(original_count) / limit)

    if request.GET.get('collapse'):
        collapsed = request.session.get('transaction_collapse')
        if collapsed == 2:
            request.session['transaction_collapse'] = 1
        else:
            request.session['transaction_collapse'] = 2

    url_params = str(request).split('/')[-1].rstrip("'>").split('&page=')[0]

    data = {'title': 'Транзакции', 'balance_holders': balance_holders, 'type_payments': type_payments,
            'transactions': transactions, 'authors': authors, 'get_param_filter': get_param_filter,
            'collapsed': collapsed, 'sub_type': sub_type, 'count': count, 'page': page, 'limit': limit,
            'url_params': url_params, 'original_count': original_count, 'coming_sum': coming_sum,
            'expenditure_amount': expenditure_amount, 'expenditure_comission': expenditure_comission,
            'expenditure_transaction': expenditure_transaction}

    return render(request, 'mainapp/transactions.html', data)


def create_transaction_view(request):

    transaction = Transaction
    form = TransactionForm
    type_payments = PayType.objects.all()
    balance_holders = []
    if request.user.is_superuser:
        balance_holders = get_allow_and_hide_balance_holders(request.user.id, simple_user=False)
    else:
        balance_holders = get_allow_and_hide_balance_holders(request.user.id, simple_user=True)

    if request.method == 'POST':
        if request.POST.get('type') == 'check_holder':
            organization_holder = request.POST.get('balance_holder')
            if BalanceHolder.objects.filter(organization_holder=organization_holder).exists():
                return JsonResponse({'message': True})
            else:
                return JsonResponse({'message': False})

        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                pay_type_element = PayType.objects.filter(pay_type=pay_type)[0].subtypes_of_the_type.all()
                sub_type_pay = []
                for i in pay_type_element:
                    sub_type_pay.append(i.sub_type)
                return JsonResponse({'message': sub_type_pay})
            else:
                return JsonResponse({'message': False})

        holder_response = request.POST.get('balance_holder')
        balance_holder_response = BalanceHolder.objects.filter(organization_holder=holder_response)
        sub_type = None
        if request.POST.get('sub_type'):
            sub_type = SubPayType.objects.filter(sub_type=request.POST.get('sub_type'))[0]
        name = request.POST.get('transaction_name')

        status = request.POST.get('transaction_status')
        if status == 'В процессе':
            status = 'INPROCESS'
        elif status == 'Отклонен':
            status = 'REJECT'
        else:
            status = 'SUCCESSFULLY'

        transaction_date = dt.strptime(request.POST.get('transaction_date'), '%d.%m.%Y').date()

        type_payment = PayType.objects.filter(pay_type=request.POST.get('type_payment'))[0]

        commission = 0
        if request.POST.get('commission_post'):
            commission = decimal.Decimal(request.POST.get('commission_post').replace(',', '.').replace(' ', ''))
        transaction_sum = decimal.Decimal(request.POST.get('transaction_sum_post').replace(',', '.').replace(' ', ''))
        amount = transaction_sum + commission

        type_transaction = request.POST.get('type_transaction')
        if type_transaction == 'Приход':
            type_transaction = 'COMING'
        else:
            type_transaction = 'EXPENDITURE'

        '''Логика для загрузки ЧЕКов'''
        image = request.FILES.get('check_img')
        if image:
            check_img = f"img/{str(image).replace(' ', '_')}"
            root = f'{settings.MEDIA_ROOT}/{str(check_img)}'
            with open(root, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)
            image = check_img

        description = request.POST.get('description')
        tags = request.POST.get('tags')

        author_id = request.user.id

        new_data = {
            'transaction_date': transaction_date, 'type_transaction': type_transaction,
            'name': name, 'description': description, 'balance_holder': balance_holder_response[0],
            'amount': amount, 'type_payment': type_payment, 'status': status, 'tags': tags,
            'check_img': image, 'author_id': author_id, 'commission': commission, 'transaction_sum': transaction_sum,
            'sub_type_pay': sub_type
        }

        transaction.objects.create(**new_data)

        old_balance_balance_holder = balance_holder_response[0].holder_balance
        if status == 'SUCCESSFULLY':
            if type_transaction == 'COMING':
                old_balance_balance_holder += amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
            else:
                old_balance_balance_holder -= amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
        else:
            pass
        return redirect('transactions')

    data = {'title': 'Создание транзакции', 'inside': {'page_url': 'transactions', 'page_title': 'Транзакции'},
            'form': form, 'type_payments': type_payments, 'balance_holders': balance_holders}

    return render(request, 'mainapp/transaction_create.html', data)


def create_transaction_holder_view(request, pk):

    transaction = Transaction
    form = TransactionForm
    type_payments = PayType.objects.all()
    balance_holders_pk = BalanceHolder.objects.filter(pk=pk)
    balance_holders = BalanceHolder.objects.all()

    if request.method == 'POST':
        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                pay_type_element = PayType.objects.filter(pay_type=pay_type)[0].subtypes_of_the_type.all()
                sub_type_pay = []
                for i in pay_type_element:
                    sub_type_pay.append(i.sub_type)
                return JsonResponse({'message': sub_type_pay})
            else:
                return JsonResponse({'message': False})

        holder_response = request.POST.get('balance_holder')

        balance_holder_response = BalanceHolder.objects.filter(organization_holder=holder_response)

        name = request.POST.get('transaction_name')

        status = request.POST.get('transaction_status')
        if status == 'В процессе':
            status = 'INPROCESS'
        elif status == 'Отклонен':
            status = 'REJECT'
        else:
            status = 'SUCCESSFULLY'

        transaction_date = dt.strptime(request.POST.get('transaction_date'), '%d.%m.%Y').date()

        type_payment = PayType.objects.filter(pay_type=request.POST.get('type_payment'))[0]

        sub_type = None
        if request.POST.get('sub_type'):
            sub_type = SubPayType.objects.filter(sub_type=request.POST.get('sub_type'))[0]

        commission = 0
        if request.POST.get('commission_post'):
            commission = decimal.Decimal(request.POST.get('commission_post').replace(',', '.').replace(' ', ''))
        transaction_sum = decimal.Decimal(request.POST.get('transaction_sum_post').replace(',', '.').replace(' ', ''))
        amount = transaction_sum + commission

        type_transaction = request.POST.get('type_transaction')
        if type_transaction == 'Приход':
            type_transaction = 'COMING'
        else:
            type_transaction = 'EXPENDITURE'

        '''Логика для загрузки ЧЕКов'''
        image = request.FILES.get('check_img')
        if image:
            check_img = f"img/{str(image).replace(' ', '_')}"
            root = f'{settings.MEDIA_ROOT}/{str(check_img)}'
            with open(root, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)
            image = check_img

        description = request.POST.get('description')
        tags = request.POST.get('tags')

        author_id = request.user.id

        new_data = {
            'transaction_date': transaction_date, 'type_transaction': type_transaction,
            'name': name, 'description': description, 'balance_holder': balance_holder_response[0],
            'amount': amount, 'type_payment': type_payment, 'status': status, 'tags': tags,
            'check_img': image, 'author_id': author_id, 'commission': commission, 'transaction_sum': transaction_sum,
            'sub_type_pay': sub_type
        }

        transaction.objects.create(**new_data)

        old_balance_balance_holder = balance_holder_response[0].holder_balance
        if status == 'SUCCESSFULLY':
            if type_transaction == 'COMING':
                old_balance_balance_holder += amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
            else:
                old_balance_balance_holder -= amount
                balance_holder_response.update(holder_balance=old_balance_balance_holder)
        else:
            pass
        return redirect('transactions')

    data = {'title': 'Создание транзакции', 'inside': {'page_url': 'transactions', 'page_title': 'Транзакции'},
            'form': form, 'type_payments': type_payments, 'balance_holders': balance_holders,
            'holder_pk': balance_holders_pk[0]}

    return render(request, 'mainapp/transaction_holder_create.html', data)


def transaction_update_view(request, pk):

    transaction = Transaction.objects.filter(pk=pk)
    form_class = TransactionUpdateForm(request.POST, request.FILES)
    type_payments = PayType.objects.all()
    sub_type_of_type = type_payments.filter(pay_type=transaction[0].type_payment)[0].subtypes_of_the_type.all()

    old_transaction = transaction.values(
        'status', 'transaction_date', 'amount', 'description', 'type_payment', 'check_img', 'sub_type_pay'
    )
    if request.method == 'POST':
        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                pay_type_element = PayType.objects.filter(pay_type=pay_type)[0].subtypes_of_the_type.all()
                sub_type_pay = []
                for i in pay_type_element:
                    sub_type_pay.append(i.sub_type)
                return JsonResponse({'message': sub_type_pay})
            else:
                return JsonResponse({'message': False})

        status = request.POST.get('transaction_status')

        '''Данные через форму'''
        transaction_date = dt.strptime(request.POST.get('transaction_date'), '%d.%m.%Y').date()
        amount = decimal.Decimal(request.POST.get('amount').replace(',', '.').replace(' ', ''))
        type_payment = PayType.objects.filter(pay_type=request.POST.get('type_payment'))[0].pk
        sub_type = None
        if request.POST.get('sub_type'):
            sub_type = SubPayType.objects.filter(sub_type=request.POST.get('sub_type'))[0].pk

        '''Логика для загрузки ЧЕКов'''
        check_img = ''
        image = request.FILES.get('check_img')
        if image:
            check_img = f"img/{str(image).replace(' ', '_')}"
            root = f'{settings.MEDIA_ROOT}/{str(check_img)}'
            with open(root, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)
        if check_img == '' or check_img is None:
            check_img = transaction[0].check_img

        description = None
        if request.POST.get('description'):
            description = request.POST.get('description')

        tags = None
        if request.POST.get('tags'):
            tags = request.POST.get('tags')

        '''Словарь новых данных по форме'''
        new_transaction_data = {'status': status, 'transaction_date': transaction_date,
                                'amount': amount, 'type_payment': type_payment, 'check_img': check_img,
                                'tags': tags, 'description': description, 'sub_type_pay': sub_type}

        id_balance_holder = transaction[0].balance_holder.id
        balance_hodler = BalanceHolder.objects.filter(pk=id_balance_holder)
        old_balance_balance_holder = balance_hodler.values('holder_balance')[0]['holder_balance']

        changes = {
            'transaction_id': pk,
            'author_references': request.user,
            'transaction_name': transaction[0].name,
            'balance_holder': balance_hodler[0].organization_holder
        }

        for k in old_transaction[0]:
            check = new_transaction_data[k] == old_transaction[0][k]
            if not check:
                if k == 'transaction_date':
                    changes[k] = str(old_transaction[0][k].strftime('%d.%m.%Y'))+"/"+str(new_transaction_data[k].strftime('%d.%m.%Y'))
                changes[k] = str(old_transaction[0][k])+"/"+str(new_transaction_data[k])

        if changes.get('transaction_date'):
            date_split = changes['transaction_date'].split('/')
            date1 = (dt.strptime(date_split[0], '%Y-%m-%d').date()).strftime('%d.%m.%Y')
            date2 = (dt.strptime(date_split[1], '%Y-%m-%d').date()).strftime('%d.%m.%Y')
            dates = f'{date1}/{date2}'
            changes['transaction_date'] = dates

        if len(changes.values()) > 4:
            TransactionLog.objects.create(**changes)

        transaction.update(update_date=dt.now())

        if transaction[0].status != 'SUCCESSFULLY':
            if status == 'SUCCESSFULLY':
                if Transaction.objects.filter(pk=transaction[0].id).values('type_transaction')[0]['type_transaction'] == 'COMING':
                    old_balance_balance_holder += transaction[0].amount
                    balance_hodler.update(holder_balance=old_balance_balance_holder)
                else:
                    old_balance_balance_holder -= transaction[0].amount
                    balance_hodler.update(holder_balance=old_balance_balance_holder)
            else:
                pass

        if status == 'SUCCESSFULLY' and (amount != old_transaction[0]['amount']):
            if Transaction.objects.filter(pk=transaction[0].id).values('type_transaction')[0]['type_transaction'] == 'COMING':
                if amount > transaction[0].amount:
                    diff = amount - transaction[0].amount
                    old_balance_balance_holder += diff
                else:
                    diff = transaction[0].amount - amount
                    old_balance_balance_holder -= diff
                balance_hodler.update(holder_balance=old_balance_balance_holder)
            else:
                if amount > transaction[0].amount:
                    diff = amount - transaction[0].amount
                    old_balance_balance_holder -= diff
                else:
                    diff = transaction[0].amount - amount
                    old_balance_balance_holder += diff
                balance_hodler.update(holder_balance=old_balance_balance_holder)

        if (transaction[0].status == 'SUCCESSFULLY') and (status != 'SUCCESSFULLY'):
            if Transaction.objects.filter(pk=transaction[0].id).values('type_transaction')[0]['type_transaction'] == 'COMING':
                if amount > transaction[0].amount:
                    old_balance_balance_holder += amount
                else:
                    old_balance_balance_holder -= amount
                balance_hodler.update(holder_balance=old_balance_balance_holder)
            else:
                if amount > transaction[0].amount:
                    old_balance_balance_holder -= amount
                else:
                    old_balance_balance_holder += amount
                balance_hodler.update(holder_balance=old_balance_balance_holder)

        transaction.update(**new_transaction_data)

        return redirect('transactions')

    data = {'title': 'Изменение транзакции', 'inside': {'page_url': 'transactions', 'page_title': 'Транзакции'},
            'form': form_class, 'transaction': transaction[0], 'type_payments': type_payments,
            'sub_type_of_type': sub_type_of_type}

    return render(request, 'mainapp/transaction_edit.html', data)


def balance_holders_views(request):
    if request.user.is_superuser:
        holders = get_allow_and_hide_balance_holders(request.user.id, simple_user=False)
    else:
        holders = get_allow_and_hide_balance_holders(request.user.id, simple_user=True)

    for hol in holders:
        bal_hold = BalanceHolder.objects.filter(pk=hol.get('id'))
        if hol.get('hidden_status'):
            hol.setdefault('available_users', bal_hold[0].available_superuser.all())
        hol.setdefault('hide_for_me', bal_hold[0].hide_for_me.all())

    if request.method == 'POST':
        if request.POST.get('type') == 'hide_for_me':
            holder_id = request.POST.get('holder_id')
            bal_hol = BalanceHolder.objects.filter(pk=holder_id)[0]
            bal_hol.hide_for_me.add(request.user.id)
            return JsonResponse({'message': 'OK'})
        elif request.POST.get('type') == 'show_for_me':
            holder_id = request.POST.get('holder_id')
            bal_hol = BalanceHolder.objects.filter(pk=holder_id)[0]
            bal_hol.hide_for_me.remove(request.user.id)
            return JsonResponse({'message': 'OK'})

    data = {'title': 'Балансодержатели', 'holders': holders}
    return render(request, 'mainapp/balance_holders.html', data)


def balance_holder_create_view(request):

    form_class = BalanceHolderForm
    users = CustomUser.objects.all()

    color_dict = {
        'lightblue': 'Светло-голубой',
        'blue': 'Голубой',
        'indigo': 'Индиго',
        'purple': 'Фиолетовый',
        'pink': 'Розовый',
        'red': 'Красный',
        'orange': 'Оранжевый',
        'yellow': 'Желтый',
        'green': 'Зеленый',
        'teal': 'Хаки',
        'cyan': 'Небесный',
        'gray': 'Серый'
    }

    type_account = {
        'CARD': 'Номер Карты',
        'SCORE': 'Номер Счета',
        'OTHER': 'Другое'
    }
    if request.method == 'POST':

        if request.POST.get('type') == 'check_holder':
            organization_holder = request.POST.get('organization_holder')
            if BalanceHolder.objects.filter(organization_holder=organization_holder).exists():
                return JsonResponse({'message': False})
            else:
                return JsonResponse({'message': True})

        holder_type = request.POST.get('holder_type')
        account_type = request.POST.get('account_type')
        organization_holder = request.POST.get('organization_holder')
        payment_account = request.POST.get('payment_account').replace(' ', '')
        color = request.POST.get('color')

        alias_holder = None
        if request.POST.get('alias_holder'):
            alias_holder = request.POST.get('alias_holder')

        holder_balance = 0
        if request.POST.get('holder_balance'):
            holder_balance = decimal.Decimal(request.POST.get('holder_balance').replace(',', '.').replace(' ', ''))

        superusers_available = request.POST.getlist('superuser_available')
        if superusers_available:
            for i in range(len(superusers_available)):
                superusers_available[i] = int(superusers_available[i])

        hide_holder = False
        if request.POST.get('hide_holder'):
            hide_holder = True

        new_balance_holder = BalanceHolder.objects.create(
            holder_type=holder_type,
            account_type=account_type,
            organization_holder=organization_holder,
            payment_account=payment_account,
            alias_holder=alias_holder,
            holder_balance=holder_balance,
            hidden_status=hide_holder,
            color=color
        )
        new_balance_holder.available_superuser.set(superusers_available)
        new_balance_holder.save()

        if hide_holder:
            new_balance_holder.available_superuser.add(request.user.id)
            new_balance_holder.save()

        if superusers_available:
            for i in superusers_available:
                available_user = CustomUser.objects.filter(pk=i)
                available_user[0].available_holders.add(new_balance_holder.pk)

        if request.user.is_superuser:
            pass
        else:
            request.user.available_holders.add(new_balance_holder.pk)

        return redirect('balance_holders')

    data = {'title': 'Создание балансодержателя', 'form': form_class, 'users': users, 'type_account': type_account,
            'inside': {'page_url': 'holders', 'page_title': 'Балансодержатели'}, 'color_dict': color_dict}

    return render(request, 'mainapp/balance_holder_create.html', data)


def balance_holder_update_view(request, pk):

    users = CustomUser.objects.all()
    update_balance_holder = BalanceHolder.objects.filter(pk=pk)

    color_dict = {
        'lightblue': 'Светло-голубой',
        'blue': 'Голубой',
        'indigo': 'Индиго',
        'purple': 'Фиолетовый',
        'pink': 'Розовый',
        'red': 'Красный',
        'orange': 'Оранжевый',
        'yellow': 'Желтый',
        'green': 'Зеленый',
        'teal': 'Хаки',
        'cyan': 'Небесный',
        'gray': 'Серый'
    }
    type_account = {
        'CARD': 'Номер Карты',
        'SCORE': 'Номер Счета',
        'OTHER': 'Другое'
    }
    if request.method == 'POST':

        if request.POST.get('type') == 'check_holder':
            organization_holder = request.POST.get('organization_holder')
            if BalanceHolder.objects.filter(organization_holder=organization_holder).exists():
                if BalanceHolder.objects.filter(organization_holder=organization_holder)[0] == BalanceHolder.objects.filter(pk=pk)[0]:
                    return JsonResponse({'message': True})
                return JsonResponse({'message': False})
            else:
                return JsonResponse({'message': True})

        holder_type = request.POST.get('holder_type')
        account_type = request.POST.get('account_type')
        organization_holder = request.POST.get('organization_holder')
        payment_account = request.POST.get('payment_account').replace(' ', '')
        color = request.POST.get('color')

        alias_holder = None
        if request.POST.get('alias_holder'):
            alias_holder = request.POST.get('alias_holder')

        superusers_available = request.POST.getlist('superuser_available')
        if superusers_available:
            for i in range(len(superusers_available)):
                superusers_available[i] = int(superusers_available[i])
                available_user = CustomUser.objects.filter(pk=int(superusers_available[i]))
                available_user[0].available_holders.add(pk)

        hide_holder = False
        if request.POST.get('hide_holder'):
            hide_holder = True

        update_balance_holder[0].available_superuser.set(superusers_available)
        update_balance_holder[0].save()

        if hide_holder:
            update_balance_holder[0].available_superuser.add(request.user.id)
            update_balance_holder[0].save()

        update_balance_holder.update(
            holder_type=holder_type,
            account_type=account_type,
            organization_holder=organization_holder,
            payment_account=payment_account,
            alias_holder=alias_holder,
            hidden_status=hide_holder,
            color=color
        )

        return redirect('balance_holders')

    data = {'title': 'Редактирование балансодержателя', 'users': users, 'holder': update_balance_holder[0],
            'inside': {'page_url': 'holders', 'page_title': 'Балансодержатели'}, 'color_dict': color_dict,
            'type_account': type_account}

    return render(request, 'mainapp/balance_holder_update.html', data)


def payment_type_view(request):
    pay_type = PayType.objects.all().order_by('-id')
    sub_pay_types = SubPayType.objects.all()
    if request.method == 'POST':
        '''Проверка дублирования подтипа платежа при создании '''
        if request.POST.get('type') == 'check_sub_pay_type':
            sub_type = request.POST.get('sub_type_payment')
            if SubPayType.objects.filter(sub_type=sub_type).exists():
                return JsonResponse({'message': False})
            else:
                return JsonResponse({'message': True})
        '''создание подтипа платежа'''
        if request.POST.get('type') == 'new_sub_pay_type':
            sub_type = request.POST.get('sub_type_payment')
            sub_pay = SubPayType
            sub_pay.objects.create(sub_type=sub_type)
            return JsonResponse({'status': 'ok'})

        '''Проверка дублирования типа платежа при создании '''
        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                return JsonResponse({'message': False})
            else:
                return JsonResponse({'message': True})
        '''Создание типа платежа, с привязкой доп параметров при выборе'''
        if request.POST.get('type') == 'new_pay_type':
            pay_type = request.POST.get('type_payment')

            new_pay_type = PayType.objects.create(pay_type=pay_type)

            if request.POST.getlist('sub_type_payments[]'):
                sub_type_pay = request.POST.getlist('sub_type_payments[]')
                for i in sub_type_pay:
                    new_pay_type.subtypes_of_the_type.add(int(i))

            new_pay_type.save()
            return JsonResponse({'status': 'ok'})

        '''Выдача конкретного типа платежа для его редактирования'''
        if request.POST.get('type') == 'get_type_pay':
            sub_type_pay_el = PayType.objects.filter(pay_type=request.POST.get('type_pay'))[0].subtypes_of_the_type.all()
            sub_params = []
            for i in sub_type_pay_el:
                sub_params.append(i.id)

            return JsonResponse({'sub_params': sub_params})
        '''Редактирование типа платежа и добавление/удаление подтипов'''
        if request.POST.get('type') == 'add_sub_pay_type':
            pay_type = PayType.objects.filter(pay_type=request.POST.get('type_payment'))

            if request.POST.getlist('sub_type_payments[]'):
                sub_type_pay = request.POST.getlist('sub_type_payments[]')
                for i in range(len(sub_type_pay)):
                    sub_type_pay[i] = int(sub_type_pay[i])
                pay_type[0].subtypes_of_the_type.set(sub_type_pay)
            else:
                pay_type[0].subtypes_of_the_type.set([])

            pay_type[0].save()
            return JsonResponse({'status': 'ok'})

    data = {'title': 'Категории платежей', 'pay_type': pay_type, 'sub_pay_types': sub_pay_types}

    return render(request, 'mainapp/payments_type.html', data)


def additional_data_transaction_view(request):
    additional = ''
    if request.user.is_superuser:
        additional = get_allow_additional_transactions(request.user.id)
    else:
        additional = get_allow_additional_transactions(request.user.id, simple_user=True)

    data = {'title': 'Дополнительные данные по транзакциям', 'additional': additional}

    return render(request, 'mainapp/additional_data_transactions.html', data)


def additional_transaction_data_create_view(request):
    transactions = ''

    if request.user.is_superuser:
        transactions = get_allow_transaction_filter(request.user.id)
    else:
        transactions = get_allow_transaction_filter(request.user.id, author_res=True)

    if request.method == 'POST':
        if request.POST.get('type') == 'get_transaction_id':
            transaction_id = request.POST.get('transaction').split(',')[0]
            result = set()

            for transaction in transactions:
                result.add(str(transaction_id) == f'{transaction.get("id")}: {transaction.get("name")}')

            if any(result):
                return JsonResponse(
                        {'message': True}
                    )
            else:
                return JsonResponse(
                    {'message': False}
                )
        tr_id = request.POST.get('transaction').split(':')[0]
        transaction_id = Transaction.objects.filter(pk=tr_id)[0]
        additional_data = request.POST.get('notes_transaction')
        bal_hold = request.POST.get('transaction').split(', ')[1]
        bal_hold = BalanceHolder.objects.filter(organization_holder=bal_hold)
        AdditionalDataTransaction.objects.create(transaction_id=transaction_id,
                                                 notes=additional_data,
                                                 balance_holder_id=bal_hold[0])

        return redirect('additional_data')

    data = {'title': 'Создание дополнительных данных по транзакции', 'transactions': transactions,
            'inside': {'page_url': 'additional-data', 'page_title': 'Дополнительные данные по транзакциям '},
            }

    return render(request, 'mainapp/additional_data_transaction_create.html', data)


def transactions_log_view(request):

    limit = request.session.get("limit_transaction_logs")
    if not limit:
        request.session["limit_transaction_logs"] = 25
    try:
        page = int(request.GET.get('page'))
    except:
        page = None
    if not page:
        page = 1

    if request.method == "POST":
        '''Для установки лимита вывода информации'''
        if request.POST.get('type') == 'limit25':
            request.session["limit_transaction_logs"] = 25
            return HttpResponse({'status': 'OK'})
        if request.POST.get('type') == 'limit50':
            request.session["limit_transaction_logs"] = 50
            return HttpResponse({'status': 'OK'})
        if request.POST.get('type') == 'limit100':
            request.session["limit_transaction_logs"] = 100
            return HttpResponse({'status': 'OK'})

    limit = request.session["limit_transaction_logs"]
    if page == 1:
        offset = None
    elif page == 2:
        offset = limit
    else:
        offset = limit * (page - 1)
    request.session['offset_transaction_logs'] = offset
    bal_holders = BalanceHolder.objects.all()
    users_obj = CustomUser.objects.all()

    transaction_log_list = []
    for tr in get_allow_transactions_log(limit=limit, offset=offset):
        if bal_holders.filter(organization_holder=tr.get('balance_holder')):
            holder = bal_holders.filter(organization_holder=tr.get('balance_holder'))
            if holder.values('hidden_status')[0].get('hidden_status'):
                for user_available in holder.values('available_superuser'):
                    if int(request.user.id) == int(user_available.get('available_superuser')):
                        transaction_log_list.append(tr)
            else:
                if request.user.is_superuser:
                    transaction_log_list.append(tr)
                else:
                    for bal_holder in users_obj.values('available_holders'):
                        if int(holder.values('id')[0].get('id')) == int(bal_holder.get('available_holders')):
                            transaction_log_list.append(tr)
        tr['author_references_id'] = users_obj.filter(pk=tr.get('author_references_id'))[0]

    count = 0
    original_count = 0

    url_params = str(request).split('/')[-1].rstrip("'>").split('&page=')[0]

    data = {'title': 'Логи транзакций', 'transactions_log': transaction_log_list,
            'count': count, 'page': page, 'limit': limit, 'url_params': url_params,
            'original_count': original_count}
    return render(request, 'mainapp/transactions_log.html', data)


def lock_page(request):

    '''Для подтверждения Telegram_id'''
    md5_hash = md5(f'{request.user.id}_fv3353rv23v3ve_vsfvdfvdfvdf53f3_e1fj43d'.encode()).hexdigest()
    user_info = CustomUser.objects.filter(pk=request.user.id)
    data = {'title': 'Привязка Telegram аккаунта',  'md5_hash': md5_hash,
            'page_name': 'Доступ ограничен', 'lock_page': 'lock_page', 'user_info': user_info}

    return render(request, 'mainapp/lock-page.html', data)


def handler404(request, exception):
    return render(request, '404.html', status=404)


def handler403(request, exception):
    return render(request, '403.html', status=403)


def handler405(request, exception):
    return render(request, '405.html', status=405)


def handler500(request):
    return render(request, '500.html', status=500)


def handler501(request):
    return render(request, '501.html', status=501)


'''не применяется'''
def payment_create_view(request):

    if request.method == 'POST':

        if request.POST.get('type') == 'check_type':
            pay_type = request.POST.get('type_payment')
            if PayType.objects.filter(pay_type=pay_type).exists():
                return JsonResponse(
                    {'message': False}
                )
            else:
                return JsonResponse(
                    {'message': True}
                )

        pay_type = request.POST.get('type_payment')
        PayType.objects.create(pay_type=pay_type)

        return redirect('pay_types')

    data = {
            'title': 'Создание типа платежа',
            'inside': {'page_url': 'pay-types', 'page_title': 'Типы платежей'},
            }
    return render(request, 'mainapp/payment_type_add.html', data)
