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
            response = f'SELECT * FROM `mainapp_transaction` t WHERE `t`.`balance_holder_id`={pk} AND `t`.`status`="SUCCESSFULLY"'
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
            response = f'SELECT SUM(`amount`) as `expenditure` FROM `mainapp_transaction` t WHERE `t`.`balance_holder_id`={pk} AND `t`.`status`="SUCCESSFULLY" AND `t`.`type_transaction`="EXPENDITURE"'
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()

    return response