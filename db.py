import sqlite3
import functools


fp = "data/cache.db"

# Декоратор который при вызове функции обновляет self.conn и self.cursor
# self.conn и self.cursor имеет свойство перестовать БЫТЬ и их нужно обновлять


def update_conn(s):
    def f(fun):
        @functools.wraps(fun)
        def wrapped(*args, **kwargs):
            conn = sqlite3.connect(s.path)
            cursor = conn.cursor()
            result = fun(cursor, *args, **kwargs)
            conn.commit()
            return result
        return wrapped
    return f


buttons_needed_to_be_update = [
    "ready_tables",
    "exe"
]


class DB:
    def __init__(self, filepath: str, tables: dict) -> None:
        self.path = filepath
        self.tables = tables
        # Using decorator update_conn to buttons that are in "func_needed_to_be_update"
        method_list = [func for func in dir(DB)]
        for i, method in enumerate(method_list):
            if callable(getattr(DB, method)) and not method.startswith("__") \
                    and method in buttons_needed_to_be_update:
                setattr(self, method, update_conn(self)(getattr(self, method)))
        # ---------------------------------------------------------------------------
        self.ready_tables()

    def ready_tables(self, cursor: sqlite3.Cursor) -> None:
        for table in self.tables:
            schema = list(map(lambda k: k + " " + self.tables[table][k], self.tables[table]))
            try:
                cursor.execute(
                    f"CREATE TABLE { table }({ ','.join(schema) })"
                )
            except Exception as e:
                pass  # table already exists

    def exe(self, cursor: sqlite3.Cursor, s: str, *args) -> sqlite3.Cursor:
        return cursor.execute(s, args)


class AdapterDB:
    def __init__(self):
        self.db = DB(
            fp,
            {
                "users": {
                    "id": "INTEGER PRIMARY KEY NOT NULL",
                    "telegram_id": "INTEGER NOT NULL UNIQUE"
                },
                "dictionary": {
                    "id": "INTEGER PRIMARY KEY NOT NULL",
                    "user_id": "INTEGER",
                    "word": "STRING"
                },
                "time_seen": {
                    "id": "INTEGER PRIMARY KEY NOT NULL",
                    "user_id": "INTEGER",
                    "last_time": "LONG"
                }
            }
        )

    def get_user_id(self, telegram_id) -> int:
        try:
            return self.db.exe(
                "SELECT id FROM users WHERE telegram_id=?", telegram_id
            ).fetchone()[0]
        except TypeError:
            return -1

    def add_new_user(self, telegram_id) -> None:
        self.db.exe(
            "INSERT INTO users(telegram_id) VALUES (?)", telegram_id
        )

    def add_word_to_dictionary_by_user_id(self, user_id, word) -> None:
        self.db.exe(
            "INSERT INTO dictionary(user_id, word) VALUES (?, ?)", user_id, word
        )

    def add_word_to_dictionary(self, telegram_id, word) -> None:
        self.add_word_to_dictionary_by_user_id(
            self.get_user_id(telegram_id),
            word
        )

    def get_dictionary_by_user_id(self, user_id: int) -> list:
        try:
            return list(map(lambda x: x[0], self.db.exe(
                "SELECT word FROM dictionary WHERE user_id=?", user_id
            ).fetchall()))
        except TypeError:
            return []

    def get_dictionary(self, telegram_id: int):
        return self.get_dictionary_by_user_id(
            self.get_user_id(telegram_id)
        )

    def get_all_users(self) -> list:
        try:
            return list(map(lambda x: x[0], self.db.exe(
                "SELECT telegram_id FROM users"
            ).fetchall()))
        except TypeError:
            return []

    def get_time_seen_by_id(self, user_id: int) -> int:
        try:
            return self.db.exe(
                "SELECT last_time FROM time_seen WHERE user_id=?",
                user_id
            ).fetchone()[0]
        except TypeError:
            return -1

    def get_time_seen(self, telegram_id: int) -> int:
        return self.get_time_seen_by_id(
            self.get_user_id(telegram_id)
        )

    def get_time_seen_from(self, t: int) -> list:
        try:
            return list(map(lambda x: x[0], self.db.exe(
                "SELECT last_time FROM time_seen WWHERE last_time>?",
                t
            ).fetchall()))
        except TypeError:
            return []

    def set_time_seen_by_user_id(self, user_id: int, time_seen: int) -> None:
        if self.get_time_seen_by_id(user_id) != -1:
            self.db.exe(
                "UPDATE time_seen SET last_time=? WHERE user_id=?",
                time_seen, user_id
            )
        self.db.exe(
            "INSERT INTO time_seen(user_id, last_time) VALUES (?, ?)",
            user_id, time_seen
        )

    def set_time_seen(self, telegram_id: int, time_seen: int) -> None:
        self.set_time_seen_by_user_id(
            self.get_user_id(telegram_id),
            time_seen
        )
