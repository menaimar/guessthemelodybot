import telebot
import emoji
import time
from commands import Commands
from db import AdapterDB
from functions import *
from sched import scheduler

minute = 60
TELEGRAM_TOKEN = open_json("secure/credentials.json")["telegram"]
bot = telebot.TeleBot(TELEGRAM_TOKEN)
db = AdapterDB()
com = Commands(bot, db)
cache_threshold = 30 * minute


def clean_cache():
    for chat_id in com.cache:

        if time.time() - com.cache[chat_id]["last_update"] >= cache_threshold:
            com.cache.pop(chat_id)


cache_cleaner_delay = minute
sch = scheduler(time.time, time.sleep)
sch.enter(cache_cleaner_delay, 1, clean_cache)


@bot.message_handler(func=lambda x: True)
def main(message):
    chat_id = message.json["chat"]["id"]
    text = emoji.demojize(message.text, use_aliases=True)
    try:
        state = com.cache[chat_id]["state"]
        print(state)
    except KeyError:
        state = states["nothing"]
    if chat_id not in com.cache:
        com.cache[chat_id] = {
            "state": states["nothing"],
            "last_update": time.time(),
            "admin": False
        }
    # Если в первый раз видим его
    if db.get_user_id(chat_id) is -1:
        db.add_new_user(chat_id)
        com.exe("start", chat_id)

    time_seen = int(time.time())
    com.cache[chat_id]["last_update"] = time_seen
    db.set_time_seen(chat_id, time_seen)

    # Команды
    if message.text.strip("/") in com.get_commands():
        command = message.text.strip("/")
        # Запускаем команду command
        com.exe(command, chat_id)
        return

    if text == "Back to menu":
        if chat_id in com.cache:
            com.cache[chat_id] = pop_keys_from_dict(com.cache[chat_id], list(com.cache[chat_id].keys()))
        com.exe("menu", chat_id)
        return

    if text in menu.keys():
        com.exe(menu[text], chat_id)
        return

    if state == states["game"]:
        com.exe("game", message)
        return

    elif state == states["settings"]:
        com.exe("changing", chat_id)
        return

    elif state == states["feedback"]:
        com.exe("gettingfeedback", chat_id)
        return

    elif state in [states["play"], states["choosing"], states["ownchoosing"]]:
        com.exe("maingame", message)
        return 


bot.polling()
