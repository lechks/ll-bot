import telebot
import sqlite3
import os

# -------------------- Настройки --------------------
TOKEN = os.getenv("TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
# ---------------------------------------------------

bot = telebot.TeleBot(TOKEN)
BOT_ID = bot.get_me().id

# -------------------- База данных SQLite --------------------
conn = sqlite3.connect("love.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS loves (
    username TEXT PRIMARY KEY,
    target TEXT,
    chat_id INTEGER
)
""")

conn.commit()

# -------------------- Функции базы --------------------
def save_love(user, target, chat_id):
    cursor.execute("""
    INSERT OR REPLACE INTO loves (username, target, chat_id)
    VALUES (?, ?, ?)
    """, (user, target, chat_id))
    conn.commit()

def get_target(user):
    cursor.execute("SELECT target FROM loves WHERE username=?", (user,))
    row = cursor.fetchone()
    return row[0] if row else None

def get_chat_id(user):
    cursor.execute("SELECT chat_id FROM loves WHERE username=?", (user,))
    row = cursor.fetchone()
    return row[0] if row else None

def count_likes(user):
    cursor.execute("""
    SELECT COUNT(*) FROM loves
    WHERE target=? AND username!=?
    """, (user, user))
    return cursor.fetchone()[0]

# -------------------- Команда /start --------------------
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Welcome to LL (Letovo Love) 💌\n"
        "Send me the @username of the person you like."
    )

# -------------------- Основная логика --------------------
@bot.message_handler(func=lambda message: True)
def handle_love(message):

    if not message.from_user.username:
        bot.reply_to(message, "You must set a Telegram username first!")
        return

    user = message.from_user.username.lower()
    user_chat_id = message.chat.id
    target = message.text.replace("@", "").strip().lower()

    if target == user:
        bot.reply_to(message, "You can't select yourself 😅")
        return

    # сохраняем
    save_love(user, target, user_chat_id)

    # уведомление админу
    if ADMIN_ID != BOT_ID:
        try:
            bot.send_message(
                ADMIN_ID,
                f"New submission:\n@{user} → @{target}"
            )
        except:
            pass

    # сразу говорим ждать
    bot.reply_to(message, "Wait for the results ⏳")

    # проверяем взаимность
    target_choice = get_target(target)

    if target_choice == user:

        target_chat_id = get_chat_id(target)

        try:
            bot.send_message(
                user_chat_id,
                f"@{target}\nmatch was made 💘"
            )
        except:
            pass

        try:
            bot.send_message(
                target_chat_id,
                f"@{user}\nmatch was made 💘"
            )
        except:
            pass

    else:

        # ещё нет ответа
        bot.send_message(
            user_chat_id,
            "We don’t know the other person's decision yet ✨"
        )

    # считаем сколько лайков получил пользователь
    likes = count_likes(user)

    if likes > 0:
        bot.send_message(
            user_chat_id,
            f"You are liked by {likes} people 💖"
        )

# -------------------- Запуск --------------------
print("LL Bot started ❤️")
bot.infinity_polling()
