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


def get_transaction_holder(pk):

    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cursor:
            response = \
                f'''
                SELECT `status`, `create_date`, `update_date`, `type_transaction`, `transaction_date`, `name`, `mainapp_balanceholder`.`organization_holder` AS `balance_holder_id`, `amount`, `mainapp_paytype`.`pay_type` AS `type_payment_id`, CONCAT(`mainapp_customuser`.`last_name`,' ', `mainapp_customuser`.`first_name`) AS `author_id`, `check_img`
                FROM `mainapp_transaction` t  
                JOIN `mainapp_balanceholder` ON (`mainapp_balanceholder`.`id` = `t`.`balance_holder_id`)
                JOIN `mainapp_paytype` ON (`mainapp_paytype`.`id` = `t`.`type_payment_id`)
                JOIN `mainapp_customuser` ON (`mainapp_customuser`.`id` = `t`.`author_id`)
                WHERE 
                `t`.`balance_holder_id`={pk} AND `t`.`status`="SUCCESSFULLY"
            '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_all_coming_sum(pk):
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
            SELECT SUM(`amount`) as `coming` 
            FROM `mainapp_transaction` t 
            WHERE 
            `t`.`status`="SUCCESSFULLY" 
            AND 
            `t`.`type_transaction`="COMING"
            '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_all_expenditure_sum(pk):
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
                SELECT SUM(`amount`) as `expenditure` 
                FROM `mainapp_transaction` mt 
                WHERE `mt`.`status`="SUCCESSFULLY" 
                AND `mt`.`type_transaction`="EXPENDITURE"
            '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_coming_sum(pk):
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
            SELECT SUM(`amount`) as `coming` 
            FROM `mainapp_transaction` t 
            WHERE 
            `t`.`balance_holder_id`={pk} 
            AND 
            `t`.`status`="SUCCESSFULLY" 
            AND 
            `t`.`type_transaction`="COMING"
            '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_expenditure_sum(pk):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        with conn.cursor() as cursor:
            response = f'''SELECT SUM(`amount`) as `expenditure` FROM `mainapp_transaction` mt WHERE `mt`.`balance_holder_id`={pk} AND `mt`.`status`="SUCCESSFULLY" AND `mt`.`type_transaction`="EXPENDITURE"'''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_balance_holders():
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
                WHERE `bh`.`id` 
                IN 
                (SELECT `ah`.`balanceholder_id` 
                    FROM 
                    `mainapp_customuser_available_holders` ah 
                    WHERE 
                    `ah`.`customuser_id` = `cu`.`id`)
                ) AS 'balanceholder_id' 
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
                FROM 
                `mainapp_customuser_available_holders` ah
                WHERE 
                `ah`.`customuser_id`={pk}
                '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_allow_balance_holders(pk):
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
                        `mb`.`id`,
                        `mb`.`organization_holder`,
                        `mb`.`alias_holder`,
                        `mb`.`holder_balance`,
                        `mb`.`payment_account`
                    FROM `mainapp_balanceholder` mb
                    WHERE id IN (SELECT `mah`.`balanceholder_id` FROM `mainapp_customuser_available_holders` mah WHERE `mah`.`customuser_id`={pk} AND `mb`.`deleted`=0)
                    '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_allow_balance_holders_transaction(pk, superuser_role=False):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)
    try:
        if superuser_role:
            with conn.cursor() as cursor:
                response = f'''
                        SELECT
                            `mb`.`organization_holder`
                        FROM `mainapp_balanceholder` mb
                        WHERE `mb`.`deleted`=0
                        '''
                cursor.execute(response)
                response = cursor.fetchall()
        else:
            with conn.cursor() as cursor:
                response = f'''
                        SELECT
                            `mb`.`organization_holder`
                        FROM `mainapp_balanceholder` mb
                        WHERE id IN (SELECT `mah`.`balanceholder_id` FROM `mainapp_customuser_available_holders` mah WHERE `mah`.`customuser_id`={pk} AND `mb`.`deleted`=0)
                        '''
                cursor.execute(response)
                response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_allow_transaction(pk):
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
                        `mt`.`id`,
                        `mt`.`balance_holder_id`,
                        `mt`.`type_transaction`,
                        `mt`.`transaction_date`,
                        `mt`.`create_date`,
                        `mt`.`update_date`,
                        `mt`.`name`,
                        (SELECT `mb`.`organization_holder` FROM `mainapp_balanceholder` mb WHERE `mt`.`balance_holder_id`=`mb`.`id`) as 'balance_holder',
                        `mt`.`amount`,
                        (SELECT `mp`.`pay_type` FROM `mainapp_paytype` mp WHERE `mt`.`type_payment_id`=`mp`.`id`) as 'type_payment',
                        (SELECT CONCAT(`mu`.`first_name`, ' ', `mu`.`last_name`) FROM `mainapp_customuser` mu WHERE `mt`.`author_id`=`mu`.`id`) as 'author',
                        `mt`.`status`,
                        `mt`.`check_img`                
                    FROM `mainapp_transaction` mt
                    WHERE `mt`.`balance_holder_id` IN (SELECT `mah`.`balanceholder_id` FROM `mainapp_customuser_available_holders` mah WHERE `mah`.`customuser_id`={pk})
                    ORDER BY `mt`.`id` DESC
                    '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_all_transactions():
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
                            `mt`.`id`,
                            `mt`.`balance_holder_id`,
                            `mt`.`type_transaction`,
                            `mt`.`transaction_date`,
                            `mt`.`create_date`,
                            `mt`.`update_date`,
                            `mt`.`name`,
                            (SELECT `mb`.`organization_holder` FROM `mainapp_balanceholder` mb WHERE `mt`.`balance_holder_id`=`mb`.`id`) as 'balance_holder',
                            `mt`.`amount`,
                            (SELECT `mp`.`pay_type` FROM `mainapp_paytype` mp WHERE `mt`.`type_payment_id`=`mp`.`id`) as 'type_payment',
                            (SELECT CONCAT(`mu`.`first_name`, ' ', `mu`.`last_name`) FROM `mainapp_customuser` mu WHERE `mt`.`author_id`=`mu`.`id`) as 'author',
                            `mt`.`status`,
                            `mt`.`check_img`                
                        FROM `mainapp_transaction` mt 
                        ORDER BY `mt`.`id` DESC
                        '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_allow_additional_transactions(pk):
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
                        CONCAT(`mat`.`transaction_id_id`,': ',`mt`.`name`) as name,
                        `mat`.`notes` 
                    FROM 
                        `mainapp_additionaldatatransaction` mat
                    JOIN 
                        `mainapp_transaction` mt
                    ON 
                        `mt`.`id`=`mat`.`transaction_id_id`
                    JOIN 
                        `mainapp_balanceholder` mb 
                    ON 
                        `mb`.`id`=`mt`.`balance_holder_id` 
                    JOIN 
                        `mainapp_customuser_available_holders` mcah 
                    ON 
                        `mcah`.`balanceholder_id`=`mb`.`id`
                    WHERE 	
                        `mcah`.`customuser_id`={pk}
                    '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_additional_transactions():
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
                        CONCAT(`mat`.`transaction_id_id`,': ', (SELECT `mt`.`name` FROM `mainapp_transaction` mt WHERE `mt`.`id`=`mat`.`transaction_id_id`)) as name,
                        `mat`.`notes`
                    FROM  `mainapp_additionaldatatransaction` mat
                    '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def filtered_transactions():
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
                        CONCAT(`mat`.`transaction_id_id`,': ', (SELECT `mt`.`name` FROM `mainapp_transaction` mt WHERE `mt`.`id`=`mat`.`transaction_id_id`)) as name,
                        `mat`.`notes`
                    FROM  `mainapp_additionaldatatransaction` mat
                    '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response


def get_allow_transaction_filter(pk, author_res=None, filter_data=None):
    conn = pymysql.connect(host=settings.DATABASES.get('default').get('HOST'),
                           user=settings.DATABASES.get('default').get('USER'),
                           password=settings.DATABASES.get('default').get('PASSWORD'),
                           db=settings.DATABASES.get('default').get('NAME'),
                           port=int(settings.DATABASES.get('default').get('PORT')),
                           charset='utf8mb4',
                           cursorclass=pymysql.cursors.DictCursor)

    filters = ''
    if author_res is None and filter_data:
        filters += 'WHERE'

    author_req = ''
    if author_res:
        author_req = \
            f'''
            WHERE `mt`.`balance_holder_id` IN 
            (SELECT `mah`.`balanceholder_id` 
                FROM `mainapp_customuser_available_holders` mah WHERE `mah`.`customuser_id`={pk}
            )
            '''

    if filter_data:
        for key, val in filter_data.items():
            if len(filters) == 5:
                if key == 'amount_start':
                    filters += f''' `mt`.`amount` >= '{val}' '''
                elif key == 'amount_end':
                    filters += f''' `mt`.`amount` <= '{val}' '''
                elif key == 'start':
                    filters += f''' `mt`.`transaction_date` >= '{val}' '''
                elif key == 'end':
                    filters += f''' `mt`.`transaction_date` <= '{val}' '''
                elif key == 'tags':
                    filters += f''' `mt`.`tags` LIKE '%{val}%' '''
                else:
                    filters += f''' `mt`.`{key}` = '{val}' '''
            else:
                if key == 'amount_start':
                    filters += f''' AND `mt`.`amount` => '{val}' '''
                elif key == 'amount_end':
                    filters += f''' AND `mt`.`amount` <= '{val}' '''
                elif key == 'start':
                    filters += f''' AND `mt`.`transaction_date` >= '{val}' '''
                elif key == 'end':
                    filters += f''' AND `mt`.`transaction_date` <= '{val}' '''
                elif key == 'tags':
                    filters += f''' AND `mt`.`tags` LIKE '%{val}%' '''
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
                            (SELECT `mp`.`pay_type` FROM `mainapp_paytype` mp WHERE `mt`.`type_payment_id`=`mp`.`id`) as 'type_payment',
                            (SELECT `mu`.`username` FROM `mainapp_customuser` mu WHERE `mt`.`author_id`=`mu`.`id`) as 'author',
                            `mt`.`status`,
                            `mt`.`check_img`                
                        FROM `mainapp_transaction` mt
                        {author_req} {filters}
                        ORDER BY `mt`.`id` DESC
                        '''
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()
    return response
