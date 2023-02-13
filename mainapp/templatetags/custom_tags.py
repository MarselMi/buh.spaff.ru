from django.template.defaulttags import register
from datetime import datetime as dt
from mainapp.models import PayType


@register.filter
def pay_type_decode(obj):
    if obj:
        slpit_object = obj.split('/')
        first_el = PayType.objects.filter(pk=slpit_object[0])[0]
        second_el = PayType.objects.filter(pk=slpit_object[1])[0]
        return f'{first_el.pay_type}/{second_el.pay_type}'
    return f'&ndash;'


@register.filter
def dash(obj):
    if obj:
        return obj
    return f'&ndash;'


@register.filter
def split_img(obj):
    if obj:
        res = obj.split('/img/')
        if len(res) > 2:
            return res[1:]
        else:
            return res


@register.filter
def replace_space(obj:str):
    return obj.replace(' ', '_')


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
def change_sum_trans(obj):
    if obj:
        changes = obj.replace(',', '.').replace(' ', '').split('/')
        return f"{numb_format(float(changes[0]))} / {numb_format(float(changes[1]))}"
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


@register.filter
def change_status(obj):
    if obj:
        stats = obj.split('/')
        return f'{trans_status(stats[0])}/{trans_status(stats[1])}'
    else:
        return f'&ndash;'


@register.filter
def enu_list(list_element):
    return enumerate(list_element)


@register.filter
def get_item(arr, key):
    try:
        value = arr[key]
    except (KeyError, TypeError):
        return 0
    return value


@register.filter
def split_holders(obj):
    result = obj.split(',')
    return result


@register.filter
def translate_type_balance_holder(obj):
    if obj == 'PRIVATE_PERSONE':
        return 'Частное лицо'
    elif obj == 'ORGANISATION':
        return 'Организация'