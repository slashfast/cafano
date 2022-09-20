import telebot
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
UNSPLASH_APP_NAME = os.getenv('UNSPLASH_APP_NAME')
UNSPLASH_API_ACCESS_TOKEN = os.getenv('UNSPLASH_API_ACCESS_TOKEN')
UNSPLASH_URL = 'https://unsplash.com'
UNSPLASH_API_URL = 'https://api.unsplash.com'
UNSPLASH_GET_RANDOM_URN = 'photos/random'
UNSPLASH_UTM_PARAMETERS = f'utm_source={UNSPLASH_APP_NAME}&utm_medium=referral'
ALLOWED_USERS_ID = json.loads(os.environ['ALLOWED_USERS_ID'])
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, parse_mode='MarkdownV2')


def keyboard():
    keyboard_selector = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    cat = telebot.types.KeyboardButton(text='🐱')
    frog = telebot.types.KeyboardButton(text='🐸')
    hedgehog = telebot.types.KeyboardButton(text='🦔')
    dog = telebot.types.KeyboardButton(text='🐶')

    keyboard_selector.add(cat, frog, hedgehog, dog)

    return keyboard_selector


def get_unsplash_random_image(query):
    return requests.get(f'{UNSPLASH_API_URL}/{UNSPLASH_GET_RANDOM_URN}?client_id={UNSPLASH_API_ACCESS_TOKEN}&query={query}').json()


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Welcome!', reply_markup=keyboard())


@bot.message_handler(content_types=['text'])
def all_messages(message):

    if message.from_user.id not in ALLOWED_USERS_ID:
        print('User isn\'nt allowed!')
        return

    match message.text:
        case '🐱':
            response_body = get_unsplash_random_image('cat')
        case '🐸':
            response_body = get_unsplash_random_image('frog')
        case '🦔':
            response_body = get_unsplash_random_image('hedgehog')
        case '🐶':
            response_body = get_unsplash_random_image('dog')
        case _:
            bot.send_message(message.chat.id, f'Send the message only from the bot keyboard\\!')
            return

    response_photo_id = response_body['id']
    response_photo_author_username = response_body['user']['username']
    response_photo_author_name = response_body['user']['name']
    response_photo_uri = response_body['urls']['small']

    print(response_photo_id, response_photo_author_username, response_photo_author_name)
    print(response_photo_uri)

    bot.send_photo(message.chat.id, response_photo_uri, f"_Photo by [{response_photo_author_name}]({UNSPLASH_URL}/@{response_photo_author_username}?{UNSPLASH_UTM_PARAMETERS}) on [Unsplash]({UNSPLASH_URL}/?{UNSPLASH_UTM_PARAMETERS})_", reply_markup=keyboard())

    print(requests.get(f'{UNSPLASH_API_URL}/photos/{response_photo_id}/download?client_id={UNSPLASH_API_ACCESS_TOKEN}'))


bot.polling(none_stop=True)
