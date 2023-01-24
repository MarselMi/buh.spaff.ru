import pymysql
from spaffaccaunting import settings


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
            response = f'SELECT * FROM `mainapp_transaction` t WHERE `t`.`balance_holder_id`={pk}'
            cursor.execute(response)
            response = cursor.fetchall()
    finally:
        conn.close()
    return response