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
                SELECT `status`, `create_date`, `update_date`, `type_transaction`, `transaction_date`, `name`, `mainapp_balanceholder`.`organization_holder` AS `balance_holder_id`, `amount`, `mainapp_paytype`.`pay_type` AS `type_payment_id`, CONCAT(`authapp_customuser`.`last_name`,' ', `authapp_customuser`.`first_name`) AS `author_id`, `check_img`
                FROM `mainapp_transaction` t  
                JOIN `mainapp_balanceholder` ON (`mainapp_balanceholder`.`id` = `t`.`balance_holder_id`)
                JOIN `mainapp_paytype` ON (`mainapp_paytype`.`id` = `t`.`type_payment_id`)
                JOIN `authapp_customuser` ON (`authapp_customuser`.`id` = `t`.`author_id`)
                WHERE 
                `t`.`balance_holder_id`={pk} AND `t`.`status`="SUCCESSFULLY"
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
            response = f'SELECT SUM(`amount`) as `coming` FROM `mainapp_transaction` t WHERE `t`.`balance_holder_id`={pk} AND `t`.`status`="SUCCESSFULLY" AND `t`.`type_transaction`="COMING"'
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
            response = f'SELECT SUM(`amount`) as `expenditure` FROM `mainapp_transaction` mt WHERE `mt`.`balance_holder_id`={pk} AND `mt`.`status`="SUCCESSFULLY" AND `mt`.`type_transaction`="EXPENDITURE"'
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response