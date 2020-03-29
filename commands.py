import emoji
import random
from functions import *


class Commands:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

        self.commands = {
            "start": self.start,
            "menu": self.menu
        }
        self.cache = {
            #states # last_seen
        }
        self.commands.update({
            x: self.__getattribute__(x) for x in dir(Commands)
            if callable(getattr(Commands, x)) and not x.startswith("__") and x not in ["get_commands", "exe"]
        })

    def get_commands(self):
        return self.commands.keys()

    def exe(self, command, *args):
        if command is None:
            return
        return self.commands[command](*args)

    def start(self, chat_id):
        self.bot.send_message(chat_id, "Привет! Это бот Угадай Мелодию! "
                                       "Ты можешь играть один, или поиграть с друзьями, добавив меня в чат!")
        self.menu(chat_id)

    def menu(self, chat_id):
        self.bot.send_message(chat_id, "Меню",
                              reply_markup=createKeyboard(2, list(map(lambda x: emoji.emojize(x, use_aliases=True),
                                                                      menu.keys()))))
        self.cache[chat_id]["state"] = states["nothing"]

    def settings(self, chat_id):
        self.bot.send_message(chat_id, reply_markup=createKeyboardWithMenu(1,
                                                                           ["Количнство вопросов", "Время для ответа"]))
        self.cache[chat_id]["state"] = states["settings"]

    def about(self, chat_id):
        self.bot.send_message(chat_id, about)

    def feedback(self, chat_id):
        self.bot.send_message(chat_id, "Оставьте ваш отзыв здесь, спасибо!")
        self.cache[chat_id]["state"] = states["about"]

    # Game
    def play(self, chat_id):
        if "questions" in self.cache[chat_id]:
            self.send_question(chat_id)
            return
        self.cache[chat_id].update({
            "state": states["play"],
            "current_question": -1,
            "total_question": 0,
            "right_answers": 0,
            "questions": []
        })
        self.bot.send_message(chat_id, "Выберите категорию", reply_markup=createKeyboardWithMenu(2, list(categories.keys()),
                                                                                                 onetime=True))
        self.cache[chat_id]["state"] = states["game"]

    def game(self, message):
        chat_id = message.json["chat"]["id"]
        category = message.text
        if category in categories:
            if type(categories[category]) is dict:
                self.bot.send_message(chat_id, "Выберите",
                                      reply_markup=createKeyboardWithMenu(2, list(categories[category].keys()), onetime=True))
                self.cache[chat_id]["category"] = category
                self.cache[chat_id]["state"] = states["choosing"]
            elif categories[category] == "own":
                self.bot.send_message(chat_id, "Отправьте ссылку на плейлист в Spotify")
                self.cache[chat_id]["state"] = states["ownchoosing"]
            else:
                self.maingame(chat_id, playlistid=categories[category])
                self.cache[chat_id]["state"] = states["play"]

    def maingame(self, smth, playlistid=0):
        text = ""
        if is_int(smth):
            chat_id = smth
        else:
            chat_id = smth.json["chat"]["id"]
            text = smth.text
        if self.cache[chat_id]["state"] == states["choosing"]:
            if type(categories[self.cache[chat_id]["category"]][text]) is list:
                playlistid = random.choice(categories[self.cache[chat_id]["category"]][text])
            else:
                playlistid = categories[self.cache[chat_id]["category"]][text]
            self.cache[chat_id]["state"] = states["play"]
        elif self.cache[chat_id]["state"] == states["ownchoosing"]:
            playlistid = text.split("playlist/")[-1].split("?")[0]
            print(playlistid)
            self.cache[chat_id]["state"] = states["play"]
        if len(self.cache[chat_id]["questions"]) == 0:
            self.cache[chat_id].update({
                "state": states["play"],
                "current_question": 0,
                "total_question": number_questions,
                "right_answers": 0,
                "questions": self.get_questions(playlistid, number_questions)
            })
            self.send_question(chat_id)
            return
        current_question = self.cache[chat_id]['current_question']
        right_answer = list(self.cache[chat_id]["questions"].keys())[current_question]
        answer = text
        if answer == right_answer:
            self.bot.send_message(chat_id, emoji.emojize("Correct :white_check_mark:", use_aliases=True))
            self.cache[chat_id]["right_answers"] += 1
        else:
            self.bot.send_message(chat_id, emoji.emojize("Incorrect :x: \n", use_aliases=True) +
                                  "Right answer is " + right_answer)

        if self.cache[chat_id]["current_question"] == self.cache[chat_id]["total_question"] - 1:
            self.cache[chat_id]["state"] = states["nothing"]
            self.bot.send_message(
                chat_id,
                f"You have finished the test! You have { self.cache[chat_id]['right_answers'] }"
                f" out of { self.cache[chat_id]['total_question'] } questions",
                reply_markup=createKeyboardWithMenu(1, [])
            )
            self.cache[chat_id] = pop_keys_from_dict(d=self.cache[chat_id], keys=[
                "current_question",
                "total_question",
                "right_answers",
                "questions"
            ])
            return
        self.cache[chat_id]["current_question"] += 1
        self.send_question(chat_id)

    def get_questions(self, id, num=10):
        quest = {}
        keys = list(songs(id).keys())
        for i in range(num):
            key = keys.pop(random.randint(0, len(keys)-1))
            quest[key] = songs(id)[key]
        return quest

    def send_question(self, chat_id):
        current_question = self.cache[chat_id]['current_question']
        cur = list(self.cache[chat_id]["questions"])[current_question]
        allsongs = open_json("data/allsongs.json")
        if cur in list(allsongs.keys()):
            self.bot.send_audio(chat_id, allsongs[cur], reply_markup=self.get_answer_keyboard(current_question, chat_id))
        else:
            m = self.bot.send_audio(channel_id, list(self.cache[chat_id]["questions"].values())[current_question])
            id = m.json["audio"]["file_id"]
            db = {cur: id}
            with open("data/allsongs.json", "r+") as file:
                data = json.load(file)
                data.update(db)
                file.seek(0)
                json.dump(data, file)
            self.bot.send_audio(
                chat_id,
                id,
                reply_markup=self.get_answer_keyboard(current_question, chat_id)
            )

    def get_answer_keyboard(self, num, chat_id, n=4, width=2):
        answers = []
        right_answer = list(self.cache[chat_id]["questions"].keys())[num]
        all = open_json("data/all.json")
        for i in range(n - 1):
            new_a = all.pop(random.randint(0, len(all)-1))
            answers.append(new_a)
        answers.append(right_answer)
        random_answers = []
        for i in range(len(answers)):
            random_answers.append(answers.pop(random.randint(0, len(answers) - 1)))
        return createKeyboardWithMenu(width, random_answers)

    def changing(self, chat_id):
        self.bot.send_message(chat_id, "Enter new number")

    def gettingfeedback(self, message):
        chat_id = message.json["chat"]["id"]
        write(message.text, str(chat_id) + ".txt")
        self.bot.send_message(chat_id, "Спасибо за отзыв!")

