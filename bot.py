import telebot
import json
import os
from datetime import datetime
from threading import Thread
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# -------------------- Настройки --------------------
TOKEN = "8040240018:AAHQRfUu0HgpLP6ywlGWzRR60ZVWIx6WHyA"
ADMIN_ID = 8040240018  # вставь свой Telegram ID
# ---------------------------------------------------

bot = telebot.TeleBot(TOKEN)
BOT_ID = bot.get_me().id
DATA_FILE = "data.json"

# -------------------- Инициализация файла данных --------------------
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

# -------------------- Работа с данными --------------------
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


# -------------------- Обработчики сообщений --------------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Welcome to LL (Letovo Love) 💌\nSend me the @username of the person you like."
    )

@bot.message_handler(func=lambda message: True)
def handle_love(message):
    if not message.from_user.username:
        bot.reply_to(message, "You must set a Telegram username first!")
        return

    user = message.from_user.username
    user_id = message.chat.id
    target = message.text.replace("@", "").strip()

    data = load_data()
    data[user] = {"target": target, "chat_id": user_id}
    save_data(data)

    # Уведомление администратору
    if ADMIN_ID != BOT_ID:
        try:
            bot.send_message(ADMIN_ID, f"New submission:\n@{user} -> @{target}")
        except Exception as e:
            print(f"Cannot send admin message: {e}")

    # -------------------- Сообщение сразу пользователю --------------------
    bot.reply_to(message, "Wait for the results ⏳")

# -------------------- Фоновая рассылка 14 февраля --------------------
def send_results():
    sent_today = False
    while True:
        now = datetime.now()
        # Проверка: 14 февраля, 00:00, и чтобы не слать повторно
        if now.month == 2 and now.day == 14 and now.hour == 0 and not sent_today:
            print("Sending LL results to all users...")
            data = load_data()
            processed = set()

            for user, info in data.items():
                if user in processed:
                    continue

                user_chat_id = info["chat_id"]
                target = info["target"]

                # Взаимный матч
                if target in data and "chat_id" in data[target]:
                    target_chat_id = data[target]["chat_id"]
                    if data[target]["target"] == user:
                        if user_chat_id != BOT_ID and target_chat_id != BOT_ID:
                            try:
                                bot.send_message(user_chat_id, f"@{target}\nmatch was made 💘")
                                bot.send_message(target_chat_id, f"@{user}\nmatch was made 💘")
                                processed.add(user)
                                processed.add(target)
                                continue
                            except Exception as e:
                                print(f"Error sending match message: {e}")

                # Односторонняя любовь
                count = 0
                for u, i in data.items():
                    if i["target"] == user and data.get(user, {}).get("target") != u:
                        if "chat_id" in i and i["chat_id"] != BOT_ID:
                            count += 1
                if count > 0:
                    try:
                        bot.send_message(user_chat_id, f"You are liked by {count} people 💖")
                    except Exception as e:
                        print(f"Error sending one-sided love: {e}")

                # Человек ещё не отправил твой никнейм
                if target in data and data[target]["target"] != user:
                    try:
                        bot.send_message(user_chat_id, "We don’t know the other person's decision yet ✨")
                    except Exception as e:
                        print(f"Error sending unknown decision: {e}")

            sent_today = True
        time.sleep(30)  # проверка каждые 30 секунд

# -------------------- Запуск бота и HTTP-сервера --------------------
if __name__ == "__main__":
    if __name__ == "__main__":
        print("LL Bot started ❤️")
        bot.infinity_polling()