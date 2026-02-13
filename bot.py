import telebot
import sqlite3
import os
import time
from datetime import datetime
from threading import Thread

# -------------------- НАСТРОЙКИ --------------------

TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(TOKEN)
BOT_ID = bot.get_me().id

DB_FILE = "love.db"

# -------------------- СОЗДАНИЕ БАЗЫ --------------------

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    target TEXT,
    chat_id INTEGER
)
""")

conn.commit()

# -------------------- ФУНКЦИИ БАЗЫ --------------------

def save_user(username, target, chat_id):
    cursor.execute("""
    INSERT OR REPLACE INTO users (username, target, chat_id)
    VALUES (?, ?, ?)
    """, (username, target, chat_id))
    conn.commit()


def get_all_users():
    cursor.execute("SELECT username, target, chat_id FROM users")
    return cursor.fetchall()


def get_user(username):
    cursor.execute("SELECT username, target, chat_id FROM users WHERE username = ?", (username,))
    return cursor.fetchone()


def count_likes(username):
    cursor.execute("""
    SELECT COUNT(*) FROM users
    WHERE target = ?
    AND username != ?
    """, (username, username))

    return cursor.fetchone()[0]


# -------------------- КОМАНДА START --------------------

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Welcome to LL (Letovo Love) 💌\nSend me the @username of the person you like."
    )


# -------------------- ОБРАБОТКА СООБЩЕНИЙ --------------------

@bot.message_handler(func=lambda message: True)
def handle_love(message):

    if not message.from_user.username:
        bot.reply_to(message, "Set a Telegram username first!")
        return

    username = message.from_user.username.lower()
    target = message.text.replace("@", "").lower().strip()
    chat_id = message.chat.id

    save_user(username, target, chat_id)

    # сообщение админу
    try:
        bot.send_message(ADMIN_ID, f"@{username} -> @{target}")
    except:
        pass

    bot.reply_to(message, "Wait for the results ⏳")


# -------------------- РАССЫЛКА РЕЗУЛЬТАТОВ --------------------

def send_results():

    already_sent = False

    while True:

        now = datetime.now()

        if now.month == 2 and now.day == 14 and now.hour == 0 and not already_sent:

            print("Sending results...")

            users = get_all_users()

            processed = set()

            for username, target, chat_id in users:

                if username in processed:
                    continue

                target_user = get_user(target)

                # MATCH
                if target_user and target_user[1] == username:

                    try:
                        bot.send_message(chat_id, f"@{target}\nMatch was made 💘")
                        bot.send_message(target_user[2], f"@{username}\nMatch was made 💘")

                        processed.add(username)
                        processed.add(target)

                    except Exception as e:
                        print(e)

                else:

                    likes = count_likes(username)

                    if likes > 0:
                        try:
                            bot.send_message(chat_id, f"You are liked by {likes} people 💖")
                        except:
                            pass

                    if target_user and target_user[1] != username:
                        try:
                            bot.send_message(chat_id, "We don’t know the other person's decision yet ✨")
                        except:
                            pass

            already_sent = True

        time.sleep(30)


# -------------------- ЗАПУСК ПОТОКА --------------------

Thread(target=send_results, daemon=True).start()


# -------------------- ЗАПУСК БОТА --------------------

print("LL Bot started ❤️")

bot.infinity_polling()
