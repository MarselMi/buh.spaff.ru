#!/usr/bin/python3.10

import decimal
import json
import time
from hashlib import md5
import telebot
from telebot import types
import requests
import datetime
from pathlib import Path

from django.core.files.storage import FileSystemStorage


BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = BASE_DIR / 'media'

local = 'http://127.0.0.1:8000'
prod = 'https://buh.spaff.ru'

PROD_DOMAIN = prod

API_TOKEN = '5655161091:AAGPrpG314RXFKJe2XJ7bCGqgrh4tn9mP54'
bot = telebot.TeleBot(API_TOKEN)
url = f"https://api.telegram.org/bot{API_TOKEN}/getUpdates"


def message_not_access(message):
    bot.send_message(message.chat.id, text='''Увы, но Вы не зарегестрированы в нашей системе''')


@bot.message_handler(commands=['start'])
def incoming_message(message):

    bot.reply_to(message, 'Привязка Telegram')
    telegram_id = message.from_user.id
    response_user = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/').content)

    user_id = ''
    for user in response_user:
        if user.get('telegram_id'):
            if int(user.get('telegram_id')) == int(telegram_id):
                user_id = user.get('id')

    if user_id:
        data_dict = {
                "transaction_name": "",
                "type_transaction": "",
                "type_payment": "",
                "sub_type": "",
                "balance_holder": "",
                "transaction_date": "",
                "transaction_sum_post": "",
                "commission_post": "",
                "transaction_status": "",
                "tags": "",
                "author_id": "",
                "check_img": ""
                }

        requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                       data={"json_create_transaction": json.dumps(data_dict)})

        buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton('Создать транзакцию')
        button2 = types.KeyboardButton(text='Помощь')
        buttons.add(button1, button2)
        bot.send_message(message.chat.id, text=f"{message.from_user.username} Выберите действие: ", reply_markup=buttons)
    else:
        user_id = message.text[-1]

        md5_hash = md5(f'{user_id}_fv3353rv23v3ve_vsfvdfvdfvdf53f3_e1fj43d'.encode()).hexdigest()+f'-{user_id}'
        if md5_hash == message.text.replace('/start st-', ''):
            try:
                json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/{user_id}/').content)

                data_dict = {
                    "transaction_name": "",
                    "type_transaction": "",
                    "type_payment": "",
                    "sub_type": "",
                    "balance_holder": "",
                    "transaction_date": "",
                    "transaction_sum_post": "",
                    "commission_post": "",
                    "transaction_status": "",
                    "tags": "",
                    "author_id": "",
                    "check_img": ""
                }

                requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                               data={'telegram_id': telegram_id, 'telegram': message.from_user.username,
                                     "json_create_transaction": json.dumps(data_dict)})

                buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                button1 = types.KeyboardButton('Создать транзакцию')
                button2 = types.KeyboardButton(text='Помощь')
                buttons.add(button1, button2)
                text = f'''Приветствую Вас {message.from_user.username}!
                
Данный бот выполняет функцию добавление транзакции.

После нажатия кнопки 'START' произошла привязка Telegram_id к Вашему аккаунту в бухгалтерии

Для создания транзакции нажмите кнопку 'Создать транзакцию', и следуйте дальнейшей инструкции.

Данные по транзакции могут вводиться через кнопки меню(при наличии), либо через поле ввода информации

Для отмены создания на любом этапе введите команду /break, /crt, /create, /h, /help
Данные команды прервут создание транзакции.

Дата вводится в формате: "dd/mm/YYYY" либо "dd-mm-YYYY" либо "dd.mm.YYYY"
Для удобства можете ввести дату без разделения символоми, пример: ddmmYYYY
                '''
                bot.send_message(message.chat.id, text=text, reply_markup=buttons)
            except:
                bot.send_message(message.chat.id, text="Некорректная ссылка перехода, привязка невозможна")
        else:
            bot.send_message(message.chat.id, text="Некорректная ссылка перехода, привязка невозможна")


@bot.message_handler(commands=['h', 'help'])
def send_welcome(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')

        buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton('Создать транзакцию')
        buttons.add(button1)
        text = f'''Инструкция

Для создания транзакции нажмите кнопку 'Создать транзакцию', и следуйте дальнейшей инструкции.

Данные по транзакции могут вводиться через кнопки меню(при наличии), либо через поле ввода информации.

Для отмены создания на любом этапе введите команду /break, /br, /create, /crt, /help, /h
Данные команды прервут создание транзакции.

Дата вводится в формате: "dd/mm/YYYY" либо "dd-mm-YYYY" либо "dd.mm.YYYY"
Для удобства можете ввести дату без разделения символоми, пример: ddmmYYYY
'''
        bot.send_message(message.chat.id, text=text, reply_markup=buttons)
    except:
        message_not_access(message)


@bot.message_handler(commands=['crt', 'create', 'break', 'br'])
def send_break_create(message):
    try:
        r = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')
        user_id = r.get('id')
        data_dict = {
            "transaction_name": "",
            "type_transaction": "",
            "type_payment": "",
            "sub_type": "",
            "balance_holder": "",
            "transaction_date": "",
            "transaction_sum_post": "",
            "commission_post": "",
            "transaction_status": "",
            "tags": "",
            "author_id": user_id,
            "check_img": ""
        }
        requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                       data={"json_create_transaction": json.dumps(data_dict)})
        buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton('Создать транзакцию')
        buttons.add(button1)
        bot.send_message(message.chat.id, text="Нажмите 'Создать транзакцию'", reply_markup=buttons)
        bot.register_next_step_handler(message, listen_messages)
    except:
        message_not_access(message)


@bot.message_handler(content_types=["text"])
def listen_messages(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')

        if message.text == '/h' or message.text == '/help':
            send_welcome(message)
        elif message.text == '/break' or message.text == '/crt' or message.text == '/create' or message.text == '/br':
            send_break_create(message)
        else:
            if message.text.lower() == 'создать транзакцию':

                button = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                miss_b = types.KeyboardButton('Пропустить')
                button.add(miss_b)
                '''Отсылаю следующее сообщение в окно чата'''
                bot.send_message(message.chat.id, text="Загрузите чек, либо нажмите кнопку \"Пропустить\"",
                                 reply_markup=button)

                '''Перенаправление в следующую функцию для получения имени транзакции'''
                bot.register_next_step_handler(message, load_check)
            else:
                message_send = "Неизвестная команда, введите команду /h либо /help, для ознакомления"
                bot.send_message(message.chat.id, text=message_send)
    except:
        message_not_access(message)


@bot.message_handler(content_types=['photo'])
def load_check(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')
        if message.text == '/h' or message.text == '/help':
            send_welcome(message)
        elif message.text == '/break' or message.text == '/crt' or message.text == '/create' or message.text == '/br':
            send_break_create(message)
        else:
            try:
                fileID = message.photo[-1].file_id
                file_info = bot.get_file(fileID)
                file_format = str(file_info.file_path).split('.')[-1]
                downloaded_file = bot.download_file(file_info.file_path)
                with open(f"{MEDIA_ROOT}/img/{fileID}.{file_format}", 'wb') as new_file:
                    new_file.write(downloaded_file)

                req = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0]
                user_id = req.get('id')
                data_dict = req.get('json_create_transaction')
                data_dict['check_img'] = f'img/{fileID}.{file_format}'
                requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                               data={'json_create_transaction': json.dumps(data_dict)})

                bot.send_message(message.chat.id, text="Имя транзакции: ")
                bot.register_next_step_handler(message, transaction_type)
            except:
                bot.send_message(message.chat.id, text="Имя транзакции: ")
                bot.register_next_step_handler(message, transaction_type)
    except:
        message_not_access(message)


def transaction_type(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')
        if message.text == '/h' or message.text == '/help':
            send_welcome(message)
        elif message.text == '/break' or message.text == '/crt' or message.text == '/create' or message.text == '/br':
            send_break_create(message)
        else:
            '''получаю имя транзакции и автора, перенаправляю на выбор типа транзакции с выводом соотв сообщ
            Начало записи данных в словарь имя и пользователь'''
            req = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0]
            data_dict = req.get('json_create_transaction')
            user_id = req.get('id')
            data_dict['transaction_name'] = message.text
            data_dict['author_id'] = user_id

            requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                           data={'json_create_transaction': json.dumps(data_dict)})

            '''обозначение и определение кнопок'''
            buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button1 = types.KeyboardButton(text='Приход')
            button2 = types.KeyboardButton(text='Расход')
            buttons.add(button1, button2)

            '''вывод кнопок с возможностью выбора типа транзакции'''
            bot.send_message(message.chat.id, "Тип транзакции: ", reply_markup=buttons)
            bot.register_next_step_handler(message, transaction_balance_holder)
    except:
        message_not_access(message)


def transaction_balance_holder(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')

        if message.text == '/h' or message.text == '/help':
            send_welcome(message)
        elif message.text == '/break' or message.text == '/crt' or message.text == '/create' or message.text == '/br':
            send_break_create(message)
        elif message.text == 'Приход' or message.text == "Расход":
            '''После типа транзакции выбор на балансодержателя'''
            req = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0]
            data_dict = req.get('json_create_transaction')
            user_id = req.get('id')
            data_dict['type_transaction'] = message.text
            requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                           data={'json_create_transaction': json.dumps(data_dict)})

            try:
                b_holders = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/bal-holders/').content)

                '''обозначение и определение кнопок в зависимости от доступных'''
                buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

                for hold in b_holders:
                    if hold.get('hidden_status'):
                        if user_id in hold.get('available_superuser'):
                            buttons.add(types.KeyboardButton(text=hold.get('organization_holder')))
                    else:
                        if req.get('is_superuser'):
                            buttons.add(types.KeyboardButton(text=hold.get('organization_holder')))
                        else:
                            if hold.get('id') in req.get('available_holders'):
                                buttons.add(types.KeyboardButton(text=hold.get('organization_holder')))

                '''вывод кнопок с возможностью выбора типа транзакции'''
                bot.send_message(message.chat.id, "Выберите балансодержателя: ", reply_markup=buttons)
                bot.register_next_step_handler(message, pay_type)
            except:
                '''вывод кнопок с возможностью выбора типа транзакции'''
                bot.send_message(message.chat.id, "Выберите балансодержателя")
                bot.register_next_step_handler(message, transaction_balance_holder)
        else:
            '''обозначение и определение кнопок'''
            buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button1 = types.KeyboardButton(text='Приход')
            button2 = types.KeyboardButton(text='Расход')
            buttons.add(button1, button2)
            '''вывод кнопок с возможностью выбора типа транзакции'''
            bot.send_message(message.chat.id, "Тип транзакции: ", reply_markup=buttons)
            bot.register_next_step_handler(message, transaction_balance_holder)
    except:
        message_not_access(message)


def pay_type(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')

        if message.text == '/h' or message.text == '/help':
            send_welcome(message)
        elif message.text == '/break' or message.text == '/crt' or message.text == '/create' or message.text == '/br':
            send_break_create(message)
        else:
            b_holders = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/bal-holders/').content)
            holders = []
            for hol in b_holders:
                holders.append(hol.get('organization_holder'))
            if message.text in holders:
                req = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0]
                data_dict = req.get('json_create_transaction')
                user_id = req.get('id')
                data_dict['balance_holder'] = message.text
                requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                               data={'json_create_transaction': json.dumps(data_dict)})

                pay_types = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/pays-type/').content)

                buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

                for type_pay in pay_types:
                    button = types.KeyboardButton(text=type_pay.get('pay_type'))
                    buttons.add(button)

                bot.send_message(message.chat.id, "Выберите тип платежа: ", reply_markup=buttons)
                bot.register_next_step_handler(message, transaction_date_or_sub_pay)
            else:
                req = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0]
                '''обозначение и определение кнопок в зависимости от доступных'''
                buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                if req.get('is_superuser'):
                    for holder in b_holders:
                        button = types.KeyboardButton(text=holder.get('organization_holder'))
                        buttons.add(button)
                else:
                    for holder in b_holders:
                        if holder.get('id') in req.get('available_holders'):
                            button = types.KeyboardButton(text=holder.get('organization_holder'))
                            buttons.add(button)
                '''вывод кнопок с возможностью выбора типа транзакции'''
                bot.send_message(message.chat.id, "Выберите балансодержателя: ", reply_markup=buttons)
                bot.register_next_step_handler(message, pay_type)
    except:
        message_not_access(message)


def transaction_date_or_sub_pay(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')

        if message.text == '/h' or message.text == '/help':
            send_welcome(message)
        elif message.text == '/break' or message.text == '/crt' or message.text == '/create' or message.text == '/br':
            send_break_create(message)
        else:
            pay_type_list = []
            pay_types = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/pays-type/').content)
            for p in pay_types:
                pay_type_list.append(p.get('pay_type'))
            if message.text in pay_type_list:
                req = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0]
                data_dict = req.get('json_create_transaction')
                user_id = req.get('id')
                data_dict['type_payment'] = message.text
                requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                               data={'json_create_transaction': json.dumps(data_dict)})

                pay_types = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/pays-type/').content)
                pay_type_id = ''
                for type_pay in pay_types:
                    if type_pay.get('pay_type') == message.text:
                        pay_type_id = type_pay.get('id')
                additional_pay = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/pays-type/{pay_type_id}/').content)
                if len(additional_pay.get('subtypes_of_the_type')):
                    buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                    sub_pay_type = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/sub-pay-type/').content)
                    for sub in sub_pay_type:
                        if sub.get('id') in additional_pay.get('subtypes_of_the_type'):
                            button = types.KeyboardButton(text=sub.get('sub_type'))
                            buttons.add(button)
                    bot.send_message(message.chat.id, "Выберите подтип платежа: ", reply_markup=buttons)
                    bot.register_next_step_handler(message, sub_type)
                else:
                    transaction_date(message)
            else:
                pay_types = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/pays-type/').content)

                buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

                for type_pay in pay_types:
                    button = types.KeyboardButton(text=type_pay.get('pay_type'))
                    buttons.add(button)

                bot.send_message(message.chat.id, "Выберите тип платежа: ", reply_markup=buttons)
                bot.register_next_step_handler(message, transaction_date_or_sub_pay)
    except:
        message_not_access(message)


def sub_type(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')

        if message.text == '/h' or message.text == '/help':
            send_welcome(message)
        elif message.text == '/break' or message.text == '/crt' or message.text == '/create' or message.text == '/br':
            send_break_create(message)
        else:
            sub_type_list = []
            sub_pay_type = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/sub-pay-type/').content)
            for i in sub_pay_type:
                sub_type_list.append(i.get('sub_type'))
            if message.text in sub_type_list:
                req = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0]
                data_dict = req.get('json_create_transaction')
                user_id = req.get('id')
                data_dict['sub_type'] = message.text
                requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                               data={'json_create_transaction': json.dumps(data_dict)})

                bot.send_message(message.chat.id, "Дата транзакции: ")
                bot.register_next_step_handler(message, transaction_sum)
            else:
                buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                for b in sub_type_list:
                    button = types.KeyboardButton(text=b)
                    buttons.add(button)
                bot.send_message(message.chat.id, "Выберите подтип платежа: ", reply_markup=buttons)
                bot.register_next_step_handler(message, sub_type)
    except:
        message_not_access(message)


def transaction_date(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')

        if message.text == '/h' or message.text == '/help':
            send_welcome(message)
        elif message.text == '/break' or message.text == '/crt' or message.text == '/create' or message.text == '/br':
            send_break_create(message)
        else:
            '''Добавление Балансодержателя и отправка даты'''
            req = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0]
            data_dict = req.get('json_create_transaction')
            user_id = req.get('id')
            data_dict['type_payment'] = message.text
            requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                           data={'json_create_transaction': json.dumps(data_dict)})

            bot.send_message(message.chat.id, "Дата транзакции: ")
            bot.register_next_step_handler(message, transaction_sum)

    except:
        message_not_access(message)


def transaction_sum(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')

        if message.text == '/h' or message.text == '/help':
            send_welcome(message)
        elif message.text == '/break' or message.text == '/crt' or message.text == '/create' or message.text == '/br':
            send_break_create(message)
        else:
            try:
                date_com = message.text.replace('-', '.').replace('/', '.')
                if len(message.text) == 8:
                    a = message.text
                    date_com = f'{a[:2]}.{a[1:3]}.{a[-4:]}'
                datetime.datetime.strptime(date_com, '%d.%m.%Y').date()
                req = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0]
                data_dict = req.get('json_create_transaction')
                user_id = req.get('id')
                data_dict['transaction_date'] = date_com
                requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                               data={'json_create_transaction': json.dumps(data_dict)})

                bot.send_message(message.chat.id, text="Сумма транзакции: ")
                if data_dict['type_transaction'] == 'Расход':
                    bot.register_next_step_handler(message, transaction_commission_sum)
                else:
                    bot.register_next_step_handler(message, finally_transaction_create_step)
            except ValueError:
                bot.send_message(message.chat.id, "Дата транзакции: ")
                bot.register_next_step_handler(message, transaction_sum)

    except:
        message_not_access(message)


def transaction_commission_sum(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')

        if message.text == '/h' or message.text == '/help':
            send_welcome(message)
        elif message.text == '/break' or message.text == '/crt' or message.text == '/create' or message.text == '/br':
            send_break_create(message)
        else:
            try:
                decimal.Decimal(message.text.replace(',', '.').replace(' ', ''))
                req = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0]
                data_dict = req.get('json_create_transaction')
                user_id = req.get('id')
                data_dict['transaction_sum_post'] = message.text
                requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                               data={'json_create_transaction': json.dumps(data_dict)})

                bot.send_message(message.chat.id, text="Комиссия, введите 0, если комиссии нет: ")
                bot.register_next_step_handler(message, finally_transaction_create_step)
            except:
                bot.send_message(message.chat.id, text="Сумма транзакции: ")
                bot.register_next_step_handler(message, transaction_commission_sum)

    except:
        message_not_access(message)


def finally_transaction_create_step(message):
    try:
        json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0].get('id')

        if message.text == '/h' or message.text == '/help':
            send_welcome(message)
        elif message.text == '/break' or message.text == '/crt' or message.text == '/create' or message.text == '/br':
            send_break_create(message)
        else:
            req = json.loads(requests.get(f'{PROD_DOMAIN}/api-v1/users/?telegram_id={message.chat.id}').content)[0]
            data_dict = req.get('json_create_transaction')
            user_id = req.get('id')
            try:
                if data_dict['type_transaction'] == 'Расход':
                    decimal.Decimal(message.text.replace(',', '.').replace(' ', ''))
                    data_dict['commission_post'] = message.text
                else:
                    decimal.Decimal(message.text.replace(',', '.').replace(' ', ''))
                    data_dict['transaction_sum_post'] = message.text

                data_dict['transaction_status'] = 'Успешно'
                buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                button1 = types.KeyboardButton('Создать транзакцию')
                buttons.add(button1)
                requests.post(f'{PROD_DOMAIN}/api-v1/transactions_view/', data=data_dict)
                data_dict = {
                    "transaction_name": "",
                    "type_transaction": "",
                    "type_payment": "",
                    "sub_type": "",
                    "balance_holder": "",
                    "transaction_date": "",
                    "transaction_sum_post": "",
                    "commission_post": "",
                    "transaction_status": "",
                    "tags": "",
                    "author_id": "",
                    "check_img": ""
                }

                requests.patch(f'{PROD_DOMAIN}/api-v1/users/{user_id}/',
                               data={'json_create_transaction': json.dumps(data_dict)})

                bot.send_message(
                    message.chat.id,
                    text="Транзакция успешно создана! Нажмите 'Создать транзакцию' для добавления новой",
                    reply_markup=buttons
                )
                bot.register_next_step_handler(message, listen_messages)
            except:
                if data_dict['type_transaction'] == 'Расход':
                    bot.send_message(message.chat.id, text="Комиссия, введите 0, если комиссии нет: ")
                    bot.register_next_step_handler(message, finally_transaction_create_step)
                else:
                    bot.send_message(message.chat.id, text="Сумма транзакции: ")
                    bot.register_next_step_handler(message, transaction_commission_sum)

    except:
        message_not_access(message)


if __name__ == '__main__':
    bot.infinity_polling()
