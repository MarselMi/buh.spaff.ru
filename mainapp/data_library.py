import pymysql
from spaffaccaunting import settings


def numb_format(balance):
    if balance is None:
        return '0'
    elif round(balance, 2) % 1 == 0:
        return '{0:,}'.format(int(balance)).replace(',', ' ')
    else:
        balance = round(balance, 2)
        return '{0:,}'.format(balance).replace(',', ' ').replace('.', ',')


# готов
def get_sum_transactions(pk, current=None, type_transaction=None, simpleuser=None, holder=None):
    '''Функция возвращает сумму всех успешных транзакций в
    зависимости от направления транзакции и валюты'''
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        allow_data_user = ''
        if simpleuser:
            allow_data_user = f'''
                AND `t`.`balance_holder_id` IN 
                    (
                        SELECT `mah`.`balanceholder_id` 
                        FROM `mainapp_customuser_available_holders` mah 
                        WHERE `mah`.`customuser_id`={pk}
                    )
                '''
        if holder:
            allow_data_user += f'''
                AND `t`.`balance_holder_id`={holder}
            '''
        with conn.cursor() as cursor:
            response = f'''
            SELECT 
                SUM(`amount`) as `coming`,
                (SELECT `pt`.`pay_type` FROM `mainapp_paytype` pt WHERE `pt`.`id` = `t`.`type_payment_id`) as `type`
            FROM `mainapp_transaction` t 
            JOIN `mainapp_balanceholder` mb
            ON `t`.`balance_holder_id`=`mb`.`id`
            WHERE IF(`mb`.`hidden_status` = 1, (`mb`.`hidden_status` = 1) AND ({pk} IN (SELECT `mbas`.`customuser_id` FROM `mainapp_balanceholder_available_superuser` mbas WHERE `mb`.`id`=`mbas`.`balanceholder_id`)), 1)
            AND `t`.`current_id_id`=(SELECT `mcc`.`id` FROM `mainapp_current` mcc WHERE `mcc`.`current_name`='{current}')
            AND `t`.`status`="SUCCESSFULLY" 
            AND `t`.`type_transaction`='{type_transaction}'
                {allow_data_user}
            AND {pk} NOT IN (SELECT `mbhm`.`customuser_id` FROM `mainapp_balanceholder_hide_for_me` mbhm WHERE `mb`.`id`=`mbhm`.`balanceholder_id`)
            GROUP BY `t`.`type_payment_id`
            '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


# готов
def get_allow_balance_holders(pk, simple_user=True):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        if simple_user:
            add_request = f'''
            AND `mb`.`id` IN (SELECT `mah`.`balanceholder_id` FROM `mainapp_customuser_available_holders` mah WHERE `mah`.`customuser_id`={pk} AND `mb`.`deleted`=0)
            '''
        else:
            add_request = ''

        with conn.cursor() as cursor:
            response = f'''
                    SELECT
                        `mb`.`id`,
                        `mb`.`organization_holder`,
                        `mb`.`alias_holder`,
                        `mb`.`payment_account`,
                        `mb`.`account_type`,
                        `mb`.`hidden_status`,
                        `mb`.`color`
                    FROM `mainapp_balanceholder` mb
                    WHERE 
                        IF(`mb`.`hidden_status` = 1, `mb`.`hidden_status` = 1 AND ({pk} IN (SELECT `mbas`.`customuser_id` FROM `mainapp_balanceholder_available_superuser` mbas WHERE `mb`.`id`=`mbas`.`balanceholder_id`)), 1)
                    AND {pk} NOT IN (SELECT `mbhm`.`customuser_id` FROM `mainapp_balanceholder_hide_for_me` mbhm WHERE `mb`.`id`=`mbhm`.`balanceholder_id`)
                    {add_request}
                    ORDER BY `mb`.`id` DESC
                    '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


# предварительно готов
def get_allow_and_hide_balance_holders(pk, simple_user=True):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        if simple_user:
            add_request = f'''
            AND `mb`.`id` IN (SELECT `mah`.`balanceholder_id` FROM `mainapp_customuser_available_holders` mah WHERE `mah`.`customuser_id`={pk} AND `mb`.`deleted`=0)
            '''
        else:
            add_request = ''

        with conn.cursor() as cursor:
            response = f'''
                    SELECT
                        `mb`.`id`,
                        `mb`.`organization_holder`,
                        `mb`.`alias_holder`,
                        `mb`.`payment_account`,
                        `mb`.`account_type`,
                        `mb`.`hidden_status`
                    FROM `mainapp_balanceholder` mb
                    WHERE 
                        IF(`mb`.`hidden_status` = 1, `mb`.`hidden_status` = 1 AND ({pk} IN (SELECT `mbas`.`customuser_id` FROM `mainapp_balanceholder_available_superuser` mbas WHERE `mb`.`id`=`mbas`.`balanceholder_id`)), 1)
                    {add_request}
                    ORDER BY `mb`.`id` DESC
                    '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_allow_transaction_filter(pk, author_res=None, filter_data=None, limit='', offset=None, order_by='`mt`.`id`'):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    if limit:
        limit = f'LIMIT {limit}'
    if offset:
        offset = f'OFFSET {offset}'
    else:
        offset = ''

    filters = ''
    if author_res is None and filter_data:
        filters += ''

    author_req = ''
    if author_res:
        author_req = f'''
                        AND `mt`.`balance_holder_id` IN 
                        (SELECT `mah`.`balanceholder_id` 
                            FROM `mainapp_customuser_available_holders` mah WHERE `mah`.`customuser_id`={pk}
                        )
                    '''
    if filter_data:
        for key, val in filter_data.items():
            if len(filters) == 5:
                if key == 'name':
                    filters += f''' `mt`.`name` LIKE '%{val}%' '''
                elif key == 'amount_start':
                    filters += f''' `mt`.`amount` >= '{val}' '''
                elif key == 'amount_end':
                    filters += f''' `mt`.`amount` <= '{val}' '''
                elif key == 'start':
                    filters += f''' `mt`.`transaction_date` >= '{val}' '''
                elif key == 'end':
                    filters += f''' `mt`.`transaction_date` <= '{val}' '''
                elif key == 'tags':
                    filters += f''' `mt`.`tags` LIKE '%{val}%' '''
                elif key == 'description':
                    filters += f''' `mt`.`description` LIKE '%{val}%' '''
                else:
                    filters += f''' `mt`.`{key}` = '{val}' '''
            else:
                if key == 'name':
                    filters += f''' AND `mt`.`name` LIKE '%{val}%' '''
                elif key == 'amount_start':
                    filters += f''' AND `mt`.`amount` >= '{val}' '''
                elif key == 'amount_end':
                    filters += f''' AND `mt`.`amount` <= '{val}' '''
                elif key == 'start':
                    filters += f''' AND `mt`.`transaction_date` >= '{val}' '''
                elif key == 'end':
                    filters += f''' AND `mt`.`transaction_date` <= '{val}' '''
                elif key == 'tags':
                    filters += f''' AND `mt`.`tags` LIKE '%{val}%' '''
                elif key == 'description':
                    filters += f''' AND `mt`.`description` LIKE '%{val}%' '''
                else:
                    filters += f''' AND `mt`.`{key}` = '{val}' '''

    try:
        with conn.cursor() as cursor:
            response = f'''
                        SELECT 
                            `mt`.`id`,
                            `mt`.`balance_holder_id`,
                            `mt`.`type_transaction`,
                            `mt`.`transaction_date`,
                            `mt`.`create_date`,
                            `mt`.`update_date`,
                            `mt`.`name`,
                            (SELECT `mb`.`organization_holder` FROM `mainapp_balanceholder` mb WHERE `mt`.`balance_holder_id`=`mb`.`id`) as 'balance_holder',
                            `mt`.`amount`,
                            `mt`.`commission`,
                            `mt`.`transaction_sum`,
                            `mt`.`channel` as 'Источник',
                            `mt`.`requisite` as 'Реквизиты',
                            (SELECT `mp`.`pay_type` FROM `mainapp_paytype` mp WHERE `mt`.`type_payment_id`=`mp`.`id`) as 'type_payment',
                            (SELECT `mu`.`username` FROM `mainapp_customuser` mu WHERE `mt`.`author_id`=`mu`.`id`) as 'author',
                            (SELECT `sb`.`sub_type` FROM `mainapp_subpaytype` sb WHERE `sb`.`id`=`mt`.`sub_type_pay_id`) as sub_type_pay_id,
                            `mt`.`status`,
                            `mt`.`check_img`,
                            (SELECT `mcc`.`current_name` FROM mainapp_current mcc WHERE `mt`.`current_id_id`=`mcc`.`id`) as 'current_transaction',
                            `mt`.`description`
                        FROM `mainapp_transaction` mt
                        JOIN 
                            `mainapp_balanceholder` mb
                        ON `mt`.`balance_holder_id`=`mb`.`id`
                        WHERE IF(`mb`.`hidden_status` = 1, (`mb`.`hidden_status` = 1) AND ({pk} IN (SELECT `mbas`.`customuser_id` FROM `mainapp_balanceholder_available_superuser` mbas WHERE `mb`.`id`=`mbas`.`balanceholder_id`)), 1)
                        {author_req} 
                        {filters}
                        AND {pk} NOT IN (SELECT `mbhm`.`customuser_id` FROM `mainapp_balanceholder_hide_for_me` mbhm WHERE `mb`.`id`=`mbhm`.`balanceholder_id`)
                        ORDER BY {order_by}
                        {limit}
                        {offset}
                        '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()
    return response


def get_count_allow_transaction_filter(pk, author_res=None, filter_data=None):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)

    filters = ''
    if author_res is None and filter_data:
        filters += ''

    author_req = ''
    if author_res:
        author_req = f'''
                        AND `mt`.`balance_holder_id` IN 
                        (SELECT `mah`.`balanceholder_id` 
                            FROM `mainapp_customuser_available_holders` mah WHERE `mah`.`customuser_id`={pk}
                        )
                    '''
    if filter_data:
        for key, val in filter_data.items():
            if len(filters) == 5:
                if key == 'name':
                    filters += f''' `mt`.`name` LIKE '%{val}%' '''
                elif key == 'amount_start':
                    filters += f''' `mt`.`amount` >= '{val}' '''
                elif key == 'amount_end':
                    filters += f''' `mt`.`amount` <= '{val}' '''
                elif key == 'start':
                    filters += f''' `mt`.`transaction_date` >= '{val}' '''
                elif key == 'end':
                    filters += f''' `mt`.`transaction_date` <= '{val}' '''
                elif key == 'tags':
                    filters += f''' `mt`.`tags` LIKE '%{val}%' '''
                elif key == 'description':
                    filters += f''' `mt`.`description` LIKE '%{val}%' '''
                else:
                    filters += f''' `mt`.`{key}` = '{val}' '''
            else:
                if key == 'name':
                    filters += f''' AND `mt`.`name` LIKE '%{val}%' '''
                elif key == 'amount_start':
                    filters += f''' AND `mt`.`amount` >= '{val}' '''
                elif key == 'amount_end':
                    filters += f''' AND `mt`.`amount` <= '{val}' '''
                elif key == 'start':
                    filters += f''' AND `mt`.`transaction_date` >= '{val}' '''
                elif key == 'end':
                    filters += f''' AND `mt`.`transaction_date` <= '{val}' '''
                elif key == 'tags':
                    filters += f''' AND `mt`.`tags` LIKE '%{val}%' '''
                elif key == 'description':
                    filters += f''' AND `mt`.`description` LIKE '%{val}%' '''
                else:
                    filters += f''' AND `mt`.`{key}` = '{val}' '''

    try:
        with conn.cursor() as cursor:
            response = f'''
                        SELECT 
                            COUNT(`mt`.`id`)             
                        FROM `mainapp_transaction` mt
                        JOIN 
                            `mainapp_balanceholder` mb
                        ON `mt`.`balance_holder_id`=`mb`.`id`
                        WHERE IF(`mb`.`hidden_status` = 1, (`mb`.`hidden_status` = 1) AND ({pk} IN (SELECT `mbas`.`customuser_id` FROM `mainapp_balanceholder_available_superuser` mbas WHERE `mb`.`id`=`mbas`.`balanceholder_id`)), 1)
                        AND {pk} NOT IN (SELECT `mbhm`.`customuser_id` FROM `mainapp_balanceholder_hide_for_me` mbhm WHERE `mb`.`id`=`mbhm`.`balanceholder_id`)
                        {author_req} {filters}
                        '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()
    return response


def get_allow_transactions_log(limit='', offset=None):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        if limit:
            limit = f'LIMIT {limit}'
        if offset:
            offset = f'OFFSET {offset}'
        else:
            offset = ''

        with conn.cursor() as cursor:
            response = f'''
                SELECT *
                FROM `mainapp_transactionlog` tl
                ORDER BY `tl`.`id` DESC
                {limit}
                {offset}
            '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_users_information():
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cursor:
            response = f'''
            SELECT 
                `cu`.`id`, 
                `cu`.`username`, 
                `cu`.`first_name`, 
                `cu`.`last_name`, 
                `cu`.`is_staff`, 
                `cu`.`is_superuser`, 
                (SELECT GROUP_CONCAT(`bh`.`organization_holder`) FROM `mainapp_balanceholder` bh 
                WHERE `bh`.`id` IN (SELECT `ah`.`balanceholder_id` FROM `mainapp_customuser_available_holders` ah 
                                    WHERE `ah`.`customuser_id` = `cu`.`id`)) AS 'balanceholder_id' 
            FROM `mainapp_customuser` cu
            '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_holders_user(pk):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cursor:
            response = f'''
                SELECT `ah`.`balanceholder_id`
                FROM `mainapp_customuser_available_holders` ah
                WHERE `ah`.`customuser_id`={pk}
            '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_allow_additional_transactions(pk, simple_user=''):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        if simple_user:
            simple_user = f'''AND `mat`.`balance_holder_id_id` IN 
                    (SELECT `mah`.`balanceholder_id` 
                        FROM `mainapp_customuser_available_holders` mah WHERE `mah`.`customuser_id`={pk}
                    )
            '''
        with conn.cursor() as cursor:
            response = f'''
                    SELECT
                        CONCAT(`mat`.`transaction_id_id`,': ',(SELECT `mt`.`name` FROM mainapp_transaction mt WHERE `mat`.`transaction_id_id`=`mt`.`id`)) as name,
                        `mat`.`notes`,
                        `mb`.`organization_holder`
                    FROM
                        `mainapp_additionaldatatransaction` mat
                    JOIN 
                        `mainapp_balanceholder` mb
                    ON `mat`.`balance_holder_id_id`=`mb`.`id`
                    WHERE IF(`mb`.`hidden_status` = 1, (`mb`.`hidden_status` = 1) AND ({pk} IN (SELECT `mbas`.`customuser_id` FROM `mainapp_balanceholder_available_superuser` mbas WHERE `mb`.`id`=`mbas`.`balanceholder_id`)), 1)
                    {simple_user}
                    ORDER BY `mat`.`id` DESC
                    '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_bdr_data(balance_holder='', start='', end=''):
    '''Для вывода информации '''
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        if start == end:
            where = f'''WHERE 
            `mbdr`.`month_year` = '{start}' '''
        elif start != end:
            where = f'''WHERE 
            `mbdr`.`month_year` >= '{start}' 
            AND
            `mbdr`.`month_year` < '{end}'
            '''
        else:
            where = ''

        balance_sql = ''
        if balance_holder:
            if where:
                balance_sql = f'''AND
                `mbdr`.`balance_holder_id_id` = {balance_holder}
                '''
            else:
                balance_sql = f'''WHERE
                `mbdr`.`balance_holder_id_id` = {balance_holder}
                '''

        with conn.cursor() as cursor:
            response = f'''
                    SELECT
                        `mbdr`.`params_data`
                    FROM `mainapp_bdrfond` mbdr
                    {where}{balance_sql}
                '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_bdr_data_holders(balance_holder_dates=''):
    '''Для вывода только ДАТЫ по балансодержателю в БДР'''
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cursor:
            response = f'''
                    SELECT
                        `mbdr`.`month_year`
                    FROM `mainapp_bdrfond` mbdr
                    WHERE
                        `mbdr`.`balance_holder_id_id` = {balance_holder_dates}
                '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_bdr_bal_holders():
    '''Для вывода Только балансодержателей в БДР'''
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cursor:
            response = f'''
                    SELECT 
                        (SELECT `mb`.`organization_holder` FROM mainapp_balanceholder mb WHERE `mb`.`id` = `mbdr`.`balance_holder_id_id`) as bal_hol
                    FROM `mainapp_bdrfond` mbdr
                    GROUP BY `bal_hol`
                '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_for_bdr_transaction(filter_data):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)

    try:
        with conn.cursor() as cursor:
            response = f'''
                        SELECT
                            `mt`.`amount`,
                            `mt`.`type_transaction`,
                            (SELECT 
                                `mp`.`pay_type` 
                            FROM 
                                `mainapp_paytype` mp 
                            WHERE 
                                `mt`.`type_payment_id`=`mp`.`id`) as 'type_payment',
                            (SELECT 
                                `sb`.`sub_type` 
                            FROM 
                                `mainapp_subpaytype` sb 
                            WHERE `sb`.`id`=`mt`.`sub_type_pay_id`) as sub_type_pay_id
                        FROM 
                            `mainapp_transaction` mt
                        WHERE 
                            `mt`.`transaction_date` >= '{filter_data.get('start')}' 
                        AND 
                            `mt`.`transaction_date` < '{filter_data.get('end')}' 
                        AND 
                            `mt`.`balance_holder_id` = '{filter_data.get('balance_holder_id')}'
                        '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()
    return response


def get_current_balance_balance_holders(balance_holder_id=None):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cursor:
            response = f'''
                SELECT 
                    (SELECT `mcc`.`current_name` FROM `mainapp_current` mcc WHERE `mc`.`current_id_id`=`mcc`.`id` ) as 'name',
                    `mc`.`balance_holder_id_id`,
                    `mc`.`holder_current_balance`
                FROM `mainapp_currentbalanceholderbalance` mc
                WHERE `mc`.`balance_holder_id_id`={balance_holder_id}
                AND `mc`.`holder_current_balance`!=0
            '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_currents():
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cursor:
            response = f'''
                SELECT 
                    `mc`.`id`,
                    `mc`.`current_name`
                FROM `mainapp_current` mc
            '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_currents_holder(balance_holder_id=None):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cursor:
            response = f'''
                SELECT 
                    `mc`.`balance_holder_id_id`,
                    `mc`.`current_id_id`,
                    (SELECT `c`.`current_name` FROM mainapp_current c WHERE `mc`.`current_id_id`=`c`.`id`) as name
                FROM `mainapp_currentbalanceholderbalance` mc
                WHERE `mc`.`balance_holder_id_id`={balance_holder_id}
            '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


# def get_all_expenditure_transactions_sum(pk, simpleuser=None, holder=None):
#     conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
#                            user=settings.DATABASES.get('default').get('USER'),
#                            password=settings.DATABASES.get('default').get('PASSWORD'),
#                            db=settings.DATABASES.get('default').get('NAME'),
#                            port=int(settings.DATABASES.get('default').get('PORT')),
#                            charset='utf8mb4',
#                            cursorclass=pymysql.cursors.DictCursor)
#     try:
#         allow_data_user = ''
#         if simpleuser:
#             allow_data_user = f'''
#                 AND `t`.`balance_holder_id` IN
#                     (
#                         SELECT `mah`.`balanceholder_id`
#                         FROM `mainapp_customuser_available_holders` mah
#                         WHERE `mah`.`customuser_id`={pk}
#                     )
#                 '''
#         if holder:
#             allow_data_user += f'''
#                 AND `t`.`balance_holder_id`={holder}
#             '''
#         with conn.cursor() as cursor:
#             response = f'''
#                 SELECT SUM(`amount`) as `expenditure`,
#                 (SELECT `pt`.`pay_type` FROM `mainapp_paytype` pt WHERE `pt`.`id` = `t`.`type_payment_id`) as `type`
#                 FROM `mainapp_transaction` t
#                 JOIN
#                     `mainapp_balanceholder` mb
#                 ON
#                     `t`.`balance_holder_id`=`mb`.`id`
#                 WHERE IF(`mb`.`hidden_status` = 1, (`mb`.`hidden_status` = 1) AND ({pk} IN (SELECT `mbas`.`customuser_id` FROM `mainapp_balanceholder_available_superuser` mbas WHERE `mb`.`id`=`mbas`.`balanceholder_id`)), 1)
#                 AND
#                     `t`.`status`="SUCCESSFULLY"
#                 AND
#                     `t`.`type_transaction`="EXPENDITURE"
#                 AND {pk} NOT IN (SELECT `mbhm`.`customuser_id` FROM `mainapp_balanceholder_hide_for_me` mbhm WHERE `mb`.`id`=`mbhm`.`balanceholder_id`)
#                 {allow_data_user}
#                 GROUP BY `t`.`type_payment_id`
#             '''
#             cursor.execute(response)
#             response = cursor.fetchall()
#     finally:
#         conn.close()
#
#     return response
#
#
# def filtered_transactions():
#     conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
#                            user=settings.DATABASES.get('default').get('USER'),
#                            password=settings.DATABASES.get('default').get('PASSWORD'),
#                            db=settings.DATABASES.get('default').get('NAME'),
#                            port=int(settings.DATABASES.get('default').get('PORT')),
#                            charset='utf8mb4',
#                            cursorclass=pymysql.cursors.DictCursor)
#     try:
#         with conn.cursor() as cursor:
#             response = f'''
#                     SELECT
#                         CONCAT(`mat`.`transaction_id_id`,': ', (SELECT `mt`.`name` FROM `mainapp_transaction` mt WHERE `mt`.`id`=`mat`.`transaction_id_id`)) as name,
#                         `mat`.`notes`
#                     FROM  `mainapp_additionaldatatransaction` mat
#                     '''
#             cursor.execute(response)
#             response = cursor.fetchall()
#     finally:
#         conn.close()
#
#     return response
#
# def get_allow_transaction(pk):
#     conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
#                            user=settings.DATABASES.get('default').get('USER'),
#                            password=settings.DATABASES.get('default').get('PASSWORD'),
#                            db=settings.DATABASES.get('default').get('NAME'),
#                            port=int(settings.DATABASES.get('default').get('PORT')),
#                            charset='utf8mb4',
#                            cursorclass=pymysql.cursors.DictCursor)
#     try:
#         with conn.cursor() as cursor:
#             response = f'''
#                     SELECT
#                         `mt`.`id`,
#                         `mt`.`balance_holder_id`,
#                         `mt`.`type_transaction`,
#                         `mt`.`transaction_date`,
#                         `mt`.`create_date`,
#                         `mt`.`update_date`,
#                         `mt`.`name`,
#                         (SELECT `mb`.`organization_holder` FROM `mainapp_balanceholder` mb WHERE `mt`.`balance_holder_id`=`mb`.`id`) as 'balance_holder',
#                         `mt`.`amount`,
#                         (SELECT `mp`.`pay_type` FROM `mainapp_paytype` mp WHERE `mt`.`type_payment_id`=`mp`.`id`) as 'type_payment',
#                         (SELECT CONCAT(`mu`.`first_name`, ' ', `mu`.`last_name`) FROM `mainapp_customuser` mu WHERE `mt`.`author_id`=`mu`.`id`) as 'author',
#                         `mt`.`status`,
#                         `mt`.`check_img`
#                     FROM `mainapp_transaction` mt
#                     WHERE `mt`.`balance_holder_id` IN (SELECT `mah`.`balanceholder_id` FROM `mainapp_customuser_available_holders` mah WHERE `mah`.`customuser_id`={pk})
#                     ORDER BY `mt`.`id` DESC
#                     '''
#             cursor.execute(response)
#             response = cursor.fetchall()
#     finally:
#         conn.close()
#
#     return response
#
#
# def get_allow_transactions_by_balance_holder(pk, superuser_role=False):
#     conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
#                            user=settings.DATABASES.get('default').get('USER'),
#                            password=settings.DATABASES.get('default').get('PASSWORD'),
#                            db=settings.DATABASES.get('default').get('NAME'),
#                            port=int(settings.DATABASES.get('default').get('PORT')),
#                            charset='utf8mb4',
#                            cursorclass=pymysql.cursors.DictCursor)
#     try:
#         if superuser_role:
#             with conn.cursor() as cursor:
#                 response = f'''
#                         SELECT
#                             `mb`.`organization_holder`
#                         FROM `mainapp_balanceholder` mb
#                         WHERE `mb`.`deleted`=0
#                         '''
#                 cursor.execute(response)
#                 response = cursor.fetchall()
#         else:
#             with conn.cursor() as cursor:
#                 response = f'''
#                         SELECT
#                             `mb`.`organization_holder`
#                         FROM `mainapp_balanceholder` mb
#                         WHERE id IN (SELECT `mah`.`balanceholder_id` FROM `mainapp_customuser_available_holders` mah WHERE `mah`.`customuser_id`={pk} AND `mb`.`deleted`=0)
#                         '''
#                 cursor.execute(response)
#                 response = cursor.fetchall()
#     finally:
#         conn.close()
#
#     return response
#
#
# def get_all_transactions_by_holder(pk):
#
#     conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
#                            user=settings.DATABASES.get('default').get('USER'),
#                            password=settings.DATABASES.get('default').get('PASSWORD'),
#                            db=settings.DATABASES.get('default').get('NAME'),
#                            port=int(settings.DATABASES.get('default').get('PORT')),
#                            charset='utf8mb4',
#                            cursorclass=pymysql.cursors.DictCursor)
#     try:
#         with conn.cursor() as cursor:
#             response = \
#                 f'''
#                 SELECT
#                     `status`,
#                     `create_date`,
#                     `update_date`,
#                     `type_transaction`,
#                     `transaction_date`,
#                     `name`,
#                     `mainapp_balanceholder`.`organization_holder` AS `balance_holder_id`,
#                     `amount`,
#                     `mainapp_paytype`.`pay_type` AS `type_payment_id`,
#                     CONCAT(`mainapp_customuser`.`last_name`,' ', `mainapp_customuser`.`first_name`) AS `author_id`,
#                     `check_img`
#                 FROM `mainapp_transaction` t
#                 JOIN `mainapp_balanceholder` ON (`mainapp_balanceholder`.`id` = `t`.`balance_holder_id`)
#                 JOIN `mainapp_paytype` ON (`mainapp_paytype`.`id` = `t`.`type_payment_id`)
#                 JOIN `mainapp_customuser` ON (`mainapp_customuser`.`id` = `t`.`author_id`)
#                 WHERE
#                 `t`.`balance_holder_id`={pk} AND `t`.`status`="SUCCESSFULLY"
#             '''
#             cursor.execute(response)
#             response = cursor.fetchall()
#     finally:
#         conn.close()
#
#     return response
#
# '''
# SELECT
#     `mb`.`id`,
#     `mb`.`organization_holder`,
#     `mb`.`alias_holder`,
#     `mb`.`holder_balance`,
#     `mb`.`payment_account`,
#     `mb`.`hidden_status`
# FROM `mainapp_balanceholder` mb
# WHERE
#     IF(`mb`.`hidden_status` = 1, `mb`.`hidden_status` = 1 AND (1 IN (SELECT `mbas`.`customuser_id` FROM `mainapp_balanceholder_available_superuser` mbas WHERE `mb`.`id`=`mbas`.`balanceholder_id`)), 1)
# ORDER BY `mb`.`id` DESC
# '''
# def get_coming_sum(pk):
#     conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
#                            user=settings.DATABASES.get('default').get('USER'),
#                            password=settings.DATABASES.get('default').get('PASSWORD'),
#                            db=settings.DATABASES.get('default').get('NAME'),
#                            port=int(settings.DATABASES.get('default').get('PORT')),
#                            charset='utf8mb4',
#                            cursorclass=pymysql.cursors.DictCursor)
#     try:
#         with conn.cursor() as cursor:
#             response = f'''
#             SELECT SUM(`amount`) as `coming`
#             FROM `mainapp_transaction` t
#             WHERE
#             `t`.`balance_holder_id`={pk}
#             AND
#             `t`.`status`="SUCCESSFULLY"
#             AND
#             `t`.`type_transaction`="COMING"
#             '''
#             cursor.execute(response)
#             response = cursor.fetchall()
#     finally:
#         conn.close()
#
#     return response
# def get_expenditure_sum(pk):
#     conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
#                            user=settings.DATABASES.get('default').get('USER'),
#                            password=settings.DATABASES.get('default').get('PASSWORD'),
#                            db=settings.DATABASES.get('default').get('NAME'),
#                            port=int(settings.DATABASES.get('default').get('PORT')),
#                            charset='utf8mb4',
#                            cursorclass=pymysql.cursors.DictCursor)
#     try:
#         with conn.cursor() as cursor:
#             response = f'''SELECT SUM(`amount`) as `expenditure` FROM `mainapp_transaction` mt WHERE `mt`.`balance_holder_id`={pk} AND `mt`.`status`="SUCCESSFULLY" AND `mt`.`type_transaction`="EXPENDITURE"'''
#             cursor.execute(response)
#             response = cursor.fetchall()
#     finally:
#         conn.close()
#
#     return response
# def get_all_transactions():
#     conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
#                            user=settings.DATABASES.get('default').get('USER'),
#                            password=settings.DATABASES.get('default').get('PASSWORD'),
#                            db=settings.DATABASES.get('default').get('NAME'),
#                            port=int(settings.DATABASES.get('default').get('PORT')),
#                            charset='utf8mb4',
#                            cursorclass=pymysql.cursors.DictCursor)
#     try:
#         with conn.cursor() as cursor:
#             response = f'''
#                         SELECT
#                             `mt`.`id`,
#                             `mt`.`balance_holder_id`,
#                             `mt`.`type_transaction`,
#                             `mt`.`transaction_date`,
#                             `mt`.`create_date`,
#                             `mt`.`update_date`,
#                             `mt`.`name`,
#                             (SELECT `mb`.`organization_holder` FROM `mainapp_balanceholder` mb WHERE `mt`.`balance_holder_id`=`mb`.`id`) as 'balance_holder',
#                             `mt`.`amount`,
#                             (SELECT `mp`.`pay_type` FROM `mainapp_paytype` mp WHERE `mt`.`type_payment_id`=`mp`.`id`) as 'type_payment',
#                             (SELECT CONCAT(`mu`.`first_name`, ' ', `mu`.`last_name`) FROM `mainapp_customuser` mu WHERE `mt`.`author_id`=`mu`.`id`) as 'author',
#                             `mt`.`status`,
#                             `mt`.`check_img`
#                         FROM `mainapp_transaction` mt
#                         ORDER BY `mt`.`id` DESC
#                         '''
#             cursor.execute(response)
#             response = cursor.fetchall()
#     finally:
#         conn.close()
#
#     return response
