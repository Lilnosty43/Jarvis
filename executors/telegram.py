import importlib
import logging
import os
import random
import string
from logging.config import dictConfig
from pathlib import Path
from typing import Union

import requests.exceptions
import telebot
from telebot import apihelper
from telebot.types import Message

from api.controller import offline_compatible
from executors import controls
from modules.database import database
from modules.models import config, models
from modules.utils import support

env = models.env

if not os.path.isfile(config.BotConfig().LOG_FILE):
    Path(config.BotConfig().LOG_FILE).touch()

importlib.reload(module=logging)

dictConfig(config.BotConfig().dict())
logger = logging.getLogger('telegram')

users_title = {}
db = database.Database(table_name='offline', columns=['key', 'value'])
offline_compatible = offline_compatible()

apihelper.SESSION_TIME_TO_LIVE = 5 * 60  # Forces session recreation after 5 minutes without any activity
bot = telebot.TeleBot(token=env.bot_token)


def greeting() -> str:
    """Returns a random greeting message.

    Returns:
        str:
        Random greeting.
    """
    return random.choice(
        ["Greetings", "Hello", "Welcome", "Bonjour", "Hey there", "What's up", "Yo", "Ssup", "Cheers", "Ciao"]
    )


def authenticate(payload: Message) -> Union[bool, None]:
    """Validates authentication using the payload received.

    Args:
        payload: Payload received from Telegram API.

    See Also:
        If authenticated, ``get_title_by_name`` is called and a title based on user's gender is stored as dict to reuse.

    Returns:
        bool: A boolean flag to indicate whether the user has been authenticated.
    """
    if payload.from_user.is_bot:
        logger.warning("/ command was sent by a bot!")
        logger.warning(payload.chat)
        bot.send_message(chat_id=payload.chat.id, text="OOPS! Bots don't deserve replies.")
        return
    if payload.chat.id not in env.bot_chat_ids or payload.chat.username not in env.bot_users:
        logger.error(f"Unauthorized chatID ({payload.chat.id}) or userName ({payload.chat.username})")
        bot.send_message(chat_id=payload.chat.id, text="401 USER UNAUTHORIZED")
        return
    logger.info(f"{payload.chat.username} :: {payload.text}")
    if not users_title.get(payload.chat.username):
        users_title[payload.chat.username] = get_title_by_name(payload.chat.first_name)
    return True


@bot.message_handler(commands=['hello', 'hi', 'heya', 'hey'])
def greet(payload: Message) -> None:
    """Sample greeting responses.

    Args:
        payload: Payload received from Telegram API.
    """
    if not authenticate(payload=payload):
        return
    bot.reply_to(message=payload, text=f"{greeting()} {payload.chat.first_name}!\n"
                                       f"Good {support.part_of_day()}! How may I be of service today?")


@bot.message_handler(commands=['start'])
def start(payload: Message) -> None:
    """Replies to the user with an introductory message.

    Args:
        payload: Payload received from Telegram API.
    """
    if not authenticate(payload=payload):
        return
    bot.reply_to(message=payload, parse_mode='markdown',
                 text=f"{greeting()} {payload.chat.first_name}!\n"
                      "I am Jarvis, a pre-programmed virtual assistant designed by Mr. Rao\n"
                      "You may start a conversation anytime using /jarvis\n\n"
                      "*Examples*\n\n"
                      "*Car Controls*\n"
                      "/jarvis start my car\n"
                      "/jarvis set my car to 66 degrees\n"
                      "/jarvis turn off my car\n"
                      "/jarvis lock my car\n"
                      "/jarvis unlock my car\n\n"
                      "*TV*\n"
                      "/jarvis launch Netflix on my tv\n"
                      "/jarvis increase the volume on my tv\n"
                      "/jarvis what's currently playing on my tv\n"
                      "/jarvis turn off on my tv\n\n"
                      "*Lights*\n"
                      "/jarvis turn on hallway lights\n"
                      "/jarvis set my hallway lights to warm\n"
                      "/jarvis set my bedroom lights to 5 percent\n"
                      "/jarvis turn off all my lights\n\n"
                      "*Some more...*\n"
                      "/jarvis do I have any meetings today?\n"
                      "/jarvis where is my iPhone 12 Pro\n"
                      "/jarvis do I have any emails?\n"
                      "/jarvis what is the weather in Detroit?\n"
                      "/jarvis get me the local news\n"
                      "/jarvis what is the meaning of Legionnaire\n"
                      "/jarvis tell a joke\n"
                      "/jarvis flip a coin for me\n")


def get_title_by_name(name: str) -> str:
    """Predicts gender by name and returns a title accordingly.

    Args:
        name: Name for which gender has to be predicted.

    Returns:
        str:
        ``mam`` if predicted to be female, ``sir`` if gender is predicted to be male or unpredicted.
    """
    logger.info(f"Identifying gender for {name}")
    response = requests.get(url=f"https://api.genderize.io/?name={name}")
    if not response.ok:
        return 'sir'
    if response.json().get('gender', 'Unidentified').lower() == 'female':
        logger.info(f"{name} has been identified as female.")
        return 'mam'
    else:
        return 'sir'


@bot.message_handler(commands=['jarvis'])
def jarvis(payload: Message) -> None:
    """Handles messages sent with the slash command ``/jarvis``.

    Args:
        payload: Payload received from Telegram API.
    """
    if not authenticate(payload=payload):
        return
    request = payload.text.replace('/jarvis', '').strip()
    if not request:
        bot.send_message(chat_id=payload.chat.id, parse_mode='markdown',
                         text=f"{greeting()} {payload.chat.first_name}\n"
                              "I cannot process an empty request.\n"
                              "Please use /start if you are unsure of what I can do.")
        return

    command = request.translate(str.maketrans('', '', string.punctuation))  # Remove punctuations from string

    if command.lower() == 'test':
        bot.send_message(chat_id=payload.chat.id, text="Test message received.")
        return

    if 'and' in command.split() or 'also' in command.split():
        bot.send_message(chat_id=payload.chat.id,
                         text="Jarvis can only process one command at a time via offline communicator.")
        return

    if 'after' in command.split():
        bot.send_message(chat_id=payload.chat.id,
                         text="Jarvis cannot perform tasks at a later time using offline communicator.")
        return

    if not any(word in command.lower() for word in offline_compatible):
        bot.send_message(chat_id=payload.chat.id,
                         text=f"'{command}' is not a part of offline communicator compatible request.\n"
                              "Using Telegram I'm limited to performing tasks that do not require an interaction")
        return

    logger.info(f'Request: {command}')

    if existing := db.cursor.execute("SELECT value from offline WHERE key=?", ('request',)).fetchone():
        bot.reply_to(message=payload,
                     text=f"Processing another offline request: '{existing[0]}'.\nPlease try again.")
        return

    db.cursor.execute(f"INSERT OR REPLACE INTO offline (key, value) VALUES {('request', command)}")
    db.connection.commit()

    while True:
        if response := db.cursor.execute("SELECT value from offline WHERE key=?", ('response',)).fetchone():
            bot.send_message(chat_id=payload.chat.id,
                             text=response[0].replace(env.title, users_title.get(payload.chat.username)))
            db.cursor.execute("DELETE FROM offline WHERE key=:key OR value=:value ",
                              {'key': 'response', 'value': response[0]})
            db.connection.commit()
            logger.info(f'Response: {response[0]}')
            return


def get_updates() -> bool:
    """Checks if bot is running by making a ``getUpdate`` call.

    Returns:
        bool:
        A flag indicating whether an instance of telebot is running.
    """
    logger.info('Running getUpdates on api.telegram.org.')
    try:
        bot.get_updates(limit=1, timeout=3, long_polling_timeout=3)
        return False
    except apihelper.ApiTelegramException as response:
        if response.error_code == 409:
            logger.warning(response.description)
            return True
        else:
            logger.error(response)
            controls.restart_control(quiet=True)


def poll_for_messages() -> None:
    """Polls for incoming messages."""
    if not env.bot_token or not env.bot_users or not env.bot_chat_ids:
        logger.info("BOT_TOKEN, BOT_CHAT_IDS and BOT_USERS are required to initiate the Telegram bot.")
        return
    if get_updates():
        return
    logger.info('Polling for incoming messages..')
    try:
        bot.polling(non_stop=True)
    except requests.exceptions.ReadTimeout as error:
        logger.error(error)
        logger.info('Restarting main module to re-trigger the process.')
        controls.restart_control(quiet=True)


if __name__ == '__main__':
    poll_for_messages()