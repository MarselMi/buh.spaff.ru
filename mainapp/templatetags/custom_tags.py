from django.template.defaulttags import register
from datetime import datetime as dt


@register.filter
def datetime_format(date_time):
    if date_time:
        return date_time.strftime('%d.%m.%Y в %H:%M:%S')
    else:
        return f'&ndash;'


@register.filter
def date_format(date_object):
    if date_object:
        return date_object.strftime('%d.%m.%Y')
    else:
        return f'&ndash;'


@register.filter
def numb_format(balance):
    if round(balance, 2) % 1 == 0:
        return '{0:,}'.format(int(balance)).replace(',', ' ')
    else:
        balance = round(balance, 2)
        return '{0:,}'.format(balance).replace(',', ' ').replace('.', ',')


@register.filter
def trans_type(obj):
    if obj == 'COMING':
        return 'Приход'
    elif obj == 'EXPENDITURE':
        return 'Расход'


@register.filter
def trans_status(obj):
    if obj == 'INPROCESS':
        return 'В процессе'
    elif obj == 'REJECT':
        return 'Отклонен'
    elif obj == 'SUCCESSFULLY':
        return 'Успешно'