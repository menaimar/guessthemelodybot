import json
import requests
from telebot import types


def open_json(s) -> dict:
    with open(s, encoding="utf-8") as f:
        return json.load(f)


SPOTIFY_TOKEN = open_json("secure/credentials.json")["spotify"]
headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": SPOTIFY_TOKEN}


menu = open_json("data/menu.json")
about = 'Made by @menaimar and @plouny'
states = open_json("data/states.json")
categories = open_json("data/categories.json")
number_questions = 10


def is_int(s):
    try:
        int(s)
        return True
    except:
        return False


def search(name, artist, stype="track"):
    url = "https://api.spotify.com/v1/search"
    params = {"q": f"track:{name} artist:{artist}", "type": stype}
    r = requests.get(url, headers=headers, params=params)
    return r.json()["tracks"]["items"][0]["preview_url"]


def songs(id):
    url = f"https://api.spotify.com/v1/playlists/{id}/tracks"
    r = requests.get(url, headers=headers)
    all = {}
    for song in r.json()["items"]:
        if song["track"]["preview_url"] is not None:
            all[" & ".join(list(map(lambda x: x["name"], song["track"]["artists"])))] = song["track"]["preview_url"]
    return all


def pop_keys_from_dict(d: dict, keys):
    if isinstance(keys, tuple) or isinstance(keys, list):
        for k in keys:
            if k != "dictionary" and k != "state":
                d.pop(k)
    else:
        d.pop(keys)
    return d


def write(text, filename):
    with open(filename, "w+") as f:
        try:
            f.write(text)
        except Exception as e:
            print(e.__repr__())


def createKeyboardWithMenu(row_width: int, args, onetime=False):
    return createKeyboard(row_width, args + ["Back to menu"], onetime)


def createKeyboard(row_width: int, args, onetime=False):
    if not is_int(row_width):
        raise TypeError
    markup = types.ReplyKeyboardMarkup(row_width=row_width, one_time_keyboard=onetime)
    btns = []
    for i in args:
        btn_i = types.KeyboardButton(i)
        btns.append(btn_i)
    markup.add(*btns)
    return markup


def emptyKeyboard():
    return types.ReplyKeyboardRemove(selective=False)
