import telebot
import requests
from telebot import types


API_TOKEN = '5655161091:AAGPrpG314RXFKJe2XJ7bCGqgrh4tn9mP54'

bot = telebot.TeleBot(API_TOKEN)

url = f"https://api.telegram.org/bot{API_TOKEN}/getUpdates"


data = {
        "transaction_name": "",
        "type_transaction": "",
        "sub_type": "",
        "balance_holder": "",
        "transaction_date": "",
        "type_payment": "",
        "transaction_status": "",
        "tags": "",
        "author_id": "",
        "commission_post": "",
        "transaction_sum_post": "",
    }


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, '''Начало''')
    telegram_id = message.from_user.id
    user_id = message.text[-1]
    requests.patch(f'http://127.0.0.1:8000/api-v1/users/{user_id}/', data={'telegram_id': telegram_id})
    buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Создать транзакцию')
    buttons.add(button1)
    bot.send_message(message.chat.id, text="Можно создать транзакцию", reply_markup=buttons)
    bot.register_next_step_handler(message, transaction_create)


@bot.message_handler(content_types=["text"])
def transaction_create(message):
    if message.text == 'Создать транзакцию':
        '''Перед заполнением стираю все данные которые были прежде'''
        for key in data:
                data[key] = ''
        '''Отсылаю следующее сообщение в окно чата'''
        bot.send_message(message.chat.id, text="Введите имя транзакции: ")
        '''Перенаправление в следующую функцию для получения имени транзакции'''
        bot.register_next_step_handler(message, transaction_type)


def transaction_type(message):
    '''получаю имя транзакции и автора, перенаправляю на выбор типа транзакции с выводом соотв сообщ'''

    '''Начало записи данных в словарь имя и пользователь'''
    if message.text != 'Создать транзакцию':
        print(message.text)
        telegram_id = message.from_user.id
        data['author_id'] = telegram_id
        data['transaction_name'] = message.text

        '''обозначение и определение кнопок'''
        buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton(text='Приход')
        button2 = types.KeyboardButton(text='Отход')
        buttons.add(button1, button2)
        '''вывод кнопок с возможностью выбора типа транзакции'''
        bot.send_message(message.chat.id, "Выберите тип транзакции: ", reply_markup=buttons)

        '''перенаправление на след функцию'''
        bot.register_next_step_handler(message, transaction_balance_holder)
        print(buttons.input_field_placeholder)
    else:
        transaction_create(message)


def transaction_balance_holder(message):
    '''После типа транзакции выбор на балансодержателя'''
    if message.text != 'Создать транзакцию':
        print(data, 'балансодержателя')
        print(message.text)
        data['type_transaction'] = message.text

        '''обозначение и определение кнопок'''
        buttons = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton(text='OOO "СПАФФ-ИТ"')
        button2 = types.KeyboardButton(text='SafeLink')
        button3 = types.KeyboardButton(text='Матюшевский Даниил Сергеевич')
        buttons.add(button1, button2, button3)

        '''вывод кнопок с возможностью выбора типа транзакции'''
        bot.send_message(message.chat.id, "Выберите балансодержателя: ", reply_markup=buttons)
        bot.register_next_step_handler(message, transaction_date)
        print(message.text)
    else:
        transaction_create(message)


def sub_pay_type(message):
    if message.text != 'Создать транзакцию':
        print(data, 'balance_holder')

        data['balance_holder'] = message.text
        buttons = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(text='Приход', callback_data='COMING')
        button2 = types.InlineKeyboardButton(text='Отход', callback_data='EXPENDITURE')
        buttons.add(button1, button2)

        bot.send_message(message.chat.id, "Выберите тип транзакции: ", reply_markup=buttons)
        bot.register_next_step_handler(message, transaction_date)
    else:
        transaction_create(message)


def transaction_date(message):
    '''Добавление Балансодержателя'''
    if message.text != 'Создать транзакцию':
        print(data, 'balance_holder')

        data['balance_holder'] = message.text
        buttons = types.InlineKeyboardMarkup()
        button1 = types.InlineKeyboardButton(text='Приход', callback_data='COMING')
        button2 = types.InlineKeyboardButton(text='Отход', callback_data='EXPENDITURE')
        buttons.add(button1, button2)

        bot.send_message(message.chat.id, "Выберите тип транзакции: ", reply_markup=buttons)
        bot.register_next_step_handler(message, transaction_date)
    else:
        transaction_create(message)


# def transaction_date(message):
#     if message.text != 'Создать транзакцию':
#         print(data, 'date')
#         data['transaction_date'] = message.text
#         bot.send_message(message.chat.id, text="Введите тип транзакции: ")
#         bot.register_next_step_handler(message, type_transaction)
#     else:
#         transaction_create(message)



# @bot.message_handler(func=lambda message: True)
# def echo_message(message):
#     bot.reply_to(message, message.text)


# @bot.message_handler(commands=['create_tr'])
# def echo_message(message):
#     # bot.reply_to(message, message.text)
#     print(message.text)

'''
{
    "transaction_date": "15.03.2023",
    "type_transaction": "Расход",
    "transaction_name": "api2",
    "balance_holder": "ООО \"СПАФФ ИТ\"",
    "type_payment": "офис",
    "transaction_status": "Успешно",
    "tags": "",
    "author_id": 2,
    "commission_post": "100.00",
    "transaction_sum_post": "3100.45",
    "sub_type": "аренда"
}
'''

bot.polling(none_stop=True, interval=0)
