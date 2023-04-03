import decimal
import json
from hashlib import md5

import telebot
from telebot import types
import requests
import datetime


API_TOKEN = '5655161091:AAGPrpG314RXFKJe2XJ7bCGqgrh4tn9mP54'

bot = telebot.TeleBot(API_TOKEN)

url = f"https://api.telegram.org/bot{API_TOKEN}/getUpdates"


data = {
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
    }


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, '''Начало''')
    telegram_id = message.from_user.id

    response_user = json.loads(requests.get(f'http://127.0.0.1:8000/api-v1/users/').content)

    user_id = ''
    for user in response_user:
        if user.get('telegram_id'):
            if int(user.get('telegram_id')) == int(telegram_id):
                user_id = user.get('id')
    if user_id:
        buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton('Создать транзакцию')
        buttons.add(button1)
        bot.send_message(message.chat.id, text="Нажмите 'Создать транзакцию'", reply_markup=buttons)
        bot.register_next_step_handler(message, transaction_create)
    else:
        user_id = message.text[-1]

        md5_hash = md5(f'{user_id}_fv3353rv23v3ve_vsfvdfvdfvdf53f3_e1fj43d'.encode()).hexdigest()+f'-{user_id}'
        if md5_hash == message.text.replace('/start st-', ''):
            try:
                request_get_user = json.loads(requests.get(f'http://127.0.0.1:8000/api-v1/users/{user_id}/').content)

                requests.patch(f'http://127.0.0.1:8000/api-v1/users/{user_id}/',
                               data={'telegram_id': telegram_id, 'telegram': message.from_user.username})
                buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
                button1 = types.KeyboardButton('Создать транзакцию')
                buttons.add(button1)
                bot.send_message(message.chat.id, text="Нажмите 'Создать транзакцию'", reply_markup=buttons)
                bot.register_next_step_handler(message, transaction_create)
            except:
                bot.send_message(message.chat.id, text="Некорректная ссылка перехода, привязка невозможна")
        else:
            bot.send_message(message.chat.id, text="Некорректная ссылка перехода, привязка невозможна")


@bot.message_handler(commands=['help'])
def send_help_message(message):
    buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('Создать транзакцию')
    buttons.add(button1)
    bot.send_message(
        message.chat.id,
        text='''
            Данный бот выполняет одну функцию - добавляет транзакции.
            После нажатия кнопки 'START' выполняетя привязка Telegram_id к Вашему аккаунту в бухгалтерии автоматически.
            Повторно данную команду выполнять не следует.
            Для начала создания транзакции введите команду /create 
            Либо нажмите кнопку 'Создать транзакцию' и последовательно следуйте инструкции.
        ''',
        reply_markup=buttons
    )


@bot.message_handler(commands=['create'])
def send_create(message):
    buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button1 = types.KeyboardButton('Создать транзакцию')
    buttons.add(button1)
    bot.send_message(message.chat.id, text="Нажмите 'Создать транзакцию'", reply_markup=buttons)
    bot.register_next_step_handler(message, transaction_create)


@bot.message_handler(content_types=["text"])
def transaction_create(message):
    if message.text.lower() == 'создать транзакцию':
        '''Перед заполнением стираю все данные которые были прежде'''
        for key in data:
                data[key] = ''
        '''Отсылаю следующее сообщение в окно чата'''
        bot.send_message(message.chat.id, text="Введите имя транзакции: ")
        '''Перенаправление в следующую функцию для получения имени транзакции'''
        bot.register_next_step_handler(message, transaction_type)


def transaction_type(message):
    '''получаю имя транзакции и автора, перенаправляю на выбор типа транзакции с выводом соотв сообщ
    Начало записи данных в словарь имя и пользователь'''

    if message.text != 'Создать транзакцию':
        telegram_id = message.from_user.id
        user_request = json.loads(requests.get('http://127.0.0.1:8000/api-v1/users/').content)
        for user_req in user_request:
            if user_req.get('telegram_id'):
                if int(user_req.get('telegram_id')) == int(telegram_id):
                    data['author_id'] = user_req.get('id')

        data['transaction_name'] = message.text

        '''обозначение и определение кнопок'''
        buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button1 = types.KeyboardButton(text='Приход')
        button2 = types.KeyboardButton(text='Отход')
        buttons.add(button1, button2)

        '''вывод кнопок с возможностью выбора типа транзакции'''
        bot.send_message(message.chat.id, "Выберите тип транзакции: ", reply_markup=buttons)
        bot.register_next_step_handler(message, transaction_balance_holder)
    else:
        transaction_create(message)


def transaction_balance_holder(message):
    '''После типа транзакции выбор на балансодержателя'''
    if message.text != 'Создать транзакцию':
        data['type_transaction'] = message.text

        b_holders = json.loads(requests.get('http://127.0.0.1:8000/api-v1/bal-holders/').content)

        user_information = json.loads(
            requests.get(f'http://127.0.0.1:8000/api-v1/users/{data.get("author_id")}/').content
        )

        '''обозначение и определение кнопок в зависимости от доступных'''
        buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        if user_information.get('is_superuser'):
            for holder in b_holders:
                button = types.KeyboardButton(text=holder.get('organization_holder'))
                buttons.add(button)
        else:
            for holder in b_holders:
                if holder.get('id') in user_information.get('available_holders'):
                    button = types.KeyboardButton(text=holder.get('organization_holder'))
                    buttons.add(button)

        '''вывод кнопок с возможностью выбора типа транзакции'''
        bot.send_message(message.chat.id, "Выберите балансодержателя: ", reply_markup=buttons)
        bot.register_next_step_handler(message, pay_type)
    else:
        transaction_create(message)


def pay_type(message):
    if message.text != 'Создать транзакцию':

        data['balance_holder'] = message.text
        pay_types = json.loads(requests.get('http://127.0.0.1:8000/api-v1/pays-type/').content)

        buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

        for type_pay in pay_types:
            button = types.KeyboardButton(text=type_pay.get('pay_type'))
            buttons.add(button)

        bot.send_message(message.chat.id, "Выберите тип платежа: ", reply_markup=buttons)
        bot.register_next_step_handler(message, transaction_date_or_sub_pay)
    else:
        transaction_create(message)


def transaction_date_or_sub_pay(message):
    if message.text != 'Создать транзакцию':
        data['type_payment'] = message.text
        pay_types = json.loads(requests.get('http://127.0.0.1:8000/api-v1/pays-type/').content)
        pay_type_id = ''
        for type_pay in pay_types:
            if type_pay.get('pay_type') == message.text:
                pay_type_id = type_pay.get('id')

        additional_pay = json.loads(requests.get(f'http://127.0.0.1:8000/api-v1/pays-type/{pay_type_id}/').content)

        if len(additional_pay.get('subtypes_of_the_type')):
            buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

            sub_pay_type = json.loads(requests.get('http://127.0.0.1:8000/api-v1/sub-pay-type/').content)
            for sub in sub_pay_type:
                if sub.get('id') in additional_pay.get('subtypes_of_the_type'):
                    button = types.KeyboardButton(text=sub.get('sub_type'))
                    buttons.add(button)

            bot.send_message(message.chat.id, "Выберите подтип платежа: ", reply_markup=buttons)
            bot.register_next_step_handler(message, sub_type)
        else:
            transaction_date(message)
    else:
        transaction_create(message)


def sub_type(message):
    if message.text != 'Создать транзакцию':

        data['sub_type'] = message.text
        bot.send_message(message.chat.id, "Дата транзакции: ")
        bot.register_next_step_handler(message, transaction_sum)
    else:
        transaction_create(message)


def transaction_date(message):
    '''Добавление Балансодержателя и отправка даты'''
    if message.text != 'Создать транзакцию':

        data['type_payment'] = message.text
        bot.send_message(message.chat.id, "Дата транзакции: ")
        bot.register_next_step_handler(message, transaction_sum)
    else:
        transaction_create(message)


def transaction_sum(message):
    if message.text != 'Создать транзакцию':
        try:
            datetime.datetime.strptime(message.text, '%d.%m.%Y').date()
            data['transaction_date'] = message.text
            bot.send_message(message.chat.id, text="Введите сумму транзакции: ")
            bot.register_next_step_handler(message, transaction_commission_sum)
        except ValueError:
            bot.send_message(message.chat.id, "Дата транзакции: ")
            bot.register_next_step_handler(message, transaction_sum)
    else:
        transaction_create(message)


def transaction_commission_sum(message):
    if message.text != 'Создать транзакцию':
        try:
            decimal.Decimal(message.text.replace(',', '.').replace(' ', ''))
            data['transaction_sum_post'] = message.text
            bot.send_message(message.chat.id, text="Введите сумму комиссии: ")
            bot.register_next_step_handler(message, finally_transaction_create_step)
        except:
            bot.send_message(message.chat.id, text="Введите сумму транзакции: ")
            bot.register_next_step_handler(message, transaction_commission_sum)
    else:
        transaction_create(message)


@bot.message_handler(content_types=['photo'])
def send_photo(message):
    pass


def finally_transaction_create_step(message):
    if message.text != 'Создать транзакцию':
        try:
            decimal.Decimal(message.text.replace(',', '.').replace(' ', ''))
            data['commission_post'] = message.text
            data['transaction_status'] = 'Успешно'
            buttons = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            button1 = types.KeyboardButton('Создать транзакцию')
            buttons.add(button1)
            request_transaction = requests.post('http://127.0.0.1:8000/api-v1/transactions_view/', data)
            response_tr = json.loads(request_transaction.content)
            bot.send_message(
                message.chat.id,
                text="Транзакция успешно создана! Нажмите 'Создать транзакцию' для добавления новой",
                reply_markup=buttons
            )
            bot.register_next_step_handler(message, transaction_create)
        except:
            bot.send_message(message.chat.id, text="Введите сумму комиссии: ")
            bot.register_next_step_handler(message, finally_transaction_create_step)
    else:
        transaction_create(message)


bot.polling(none_stop=True, interval=0)

