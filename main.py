from dataclasses import dataclass
import telebot
from telebot.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
import requests
import json
import os
from dotenv import load_dotenv
import redis
import re

db = redis.Redis(charset="utf-8", decode_responses=True)

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
UNSPLASH_APP_NAME = os.getenv('UNSPLASH_APP_NAME')
UNSPLASH_API_ACCESS_TOKEN = os.getenv('UNSPLASH_API_ACCESS_TOKEN')
ALLOWED_USERS_ID = json.loads(os.environ['ALLOWED_USERS_ID'])

UNSPLASH_URL = 'https://unsplash.com'
UNSPLASH_API_URL = 'https://api.unsplash.com'
UNSPLASH_GET_RANDOM_URN = 'photos/random'
UNSPLASH_UTM_PARAMETERS = f'utm_source={UNSPLASH_APP_NAME}&utm_medium=referral'
IMAGE_SIZES = ['raw', 'full', 'regular', 'small', 'thumb']
BUTTONS = {
    '🐱': 'cat',
    '🐸': 'frog',
    '🦔': 'hedgehog',
    '🐶': 'dog'
}
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode='MarkdownV2')


@dataclass
class Response:
    id: int
    uri: str
    name: str
    username: str


def escape_markdown2(sentence):
    return re.sub(r'\_|\*|\[|\]|\(|\)\~|\`|\>|\#|\+|\-|\=|\||\{|\}|\.|\!', lambda m: f'\\{m.group()}', sentence)


def main_keyboard():
    return ReplyKeyboardMarkup(row_width=2, resize_keyboard=True).add(*BUTTONS.keys())


def select_size_keyboard():
    buttons = []

    for size in IMAGE_SIZES:
        buttons.append(InlineKeyboardButton(size.capitalize(), callback_data=f'cb_{size}'))

    return InlineKeyboardMarkup().add(*buttons)


def get_random_image(query):
    return requests.get(
        f'{UNSPLASH_API_URL}/{UNSPLASH_GET_RANDOM_URN}?client_id={UNSPLASH_API_ACCESS_TOKEN}&query={query}').json()


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Welcome\\!', reply_markup=main_keyboard())


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    size_image_call_data = call.data[3:]
    user_id = call.from_user.id
    db_record = db.get(user_id)

    if size_image_call_data in IMAGE_SIZES and size_image_call_data != db_record:
        if db.set(user_id, size_image_call_data):
            bot.answer_callback_query(call.id, f'{call.data[3:].capitalize()} setting successfully applied')

            bot.edit_message_text(
                text=f'Select a desired size of obtained images\nCurrent setting is *{db.get(call.from_user.id).capitalize()}* size',
                chat_id=call.message.chat.id,
                message_id=call.message.message_id, reply_markup=select_size_keyboard())
    else:
        bot.answer_callback_query(call.id, f'\"{size_image_call_data.capitalize()}\" size is already applied')


@bot.message_handler(commands=['size'])
def size_settings_message(message):
    bot.send_message(
        message.chat.id,
        f'Select a desired size of obtained images\nCurrent setting is *{db.get(message.from_user.id).capitalize()}* size',
        reply_markup=select_size_keyboard())


@bot.message_handler(content_types=['text'])
def all_messages(message):
    user_id = message.from_user.id
    if user_id not in ALLOWED_USERS_ID:
        print('User isn\'nt allowed!')
        return

    if message.text in BUTTONS.keys():
        response_body = get_random_image(BUTTONS[message.text])
    else:
        bot.send_message(message.chat.id, f'Send the message only from the bot keyboard\\!')
        return

    print(db.get(user_id))
    if (image_size := db.get(user_id)) not in IMAGE_SIZES:
        image_size = 'small'

    print(type(image_size))

    response = Response(response_body['id'],
                        response_body['urls'][image_size],
                        response_body['user']['name'],
                        response_body['user']['username'])
    print(response)

    bot.send_photo(message.chat.id,
                   response.uri,
                   f"_Photo by [{escape_markdown2(response.name)}]({UNSPLASH_URL}/@{response.username}?{UNSPLASH_UTM_PARAMETERS}) \\"
                   f"on [Unsplash]({UNSPLASH_URL}/?{UNSPLASH_UTM_PARAMETERS})_",
                   reply_markup=main_keyboard())

    # print(requests.get(f'{UNSPLASH_API_URL}/photos/{response.id}/download?client_id={UNSPLASH_API_ACCESS_TOKEN}'))


bot.polling(none_stop=True)
