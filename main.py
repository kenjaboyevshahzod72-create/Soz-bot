import random
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

TOKEN = "9065960088:AAE67XmbmeWkJUOMlzNvHRnndYG0D3-7PgE"
bot = telebot.TeleBot(TOKEN)

# So'zlar bazasi
WORDS = [
    {"en": "Achievement", "uz": "Yutuq"},
    {"en": "Determine", "uz": "Aniqlamoq / Qaror qilmoq"},
    {"en": "Fluency", "uz": "Ravonlik (tilda)"},
    {"en": "Persistent", "uz": "Qat'iyatli / Tirishqoq"},
    {"en": "Improve", "uz": "Yaxshilamoq"}
]

user_data = {}

def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("📚 So'z yodlashni boshlash"))
    markup.add(KeyboardButton("📊 Natijam"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Assalomu alaykum! So'z yodlatuvchi aqlli botga xush kelibsiz.\n"
        "Bot avval so'zlarni o'rgatadi, keyin so'raydi. Xato qilsangiz, qayta yodlatadi!",
        reply_markup=get_main_menu()
    )

@bot.message_handler(func=lambda message: message.text == "📚 So'z yodlashni boshlash")
def start_learning(message):
    user_id = message.from_user.id
    user_data[user_id] = {
        "learn_list": WORDS.copy(),
        "quiz_list": WORDS.copy(),
        "learned_count": 0
    }
    send_next_word_to_learn(message.chat.id, user_id)

def send_next_word_to_learn(chat_id, user_id):
    data = user_data[user_id]
    if data["learn_list"]:
        word = data["learn_list"][0]
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Yodladim, keyingisi ➡️", callback_data="next_learn"))
        bot.send_message(
            chat_id,
            f"📖 **Yangi so'zni eslab qoling:**\n\n🇬🇧 **{word['en']}** — 🇺🇿 {word['uz']}",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(chat_id, "🎯 Ajoyib! Barcha so'zlarni ko'rib chiqdingiz. Endi ularni so'rayman!")
        ask_question(chat_id, user_id)

@bot.callback_query_handler(func=lambda call: call.data == "next_learn")
def process_next_learn(call):
    user_id = call.from_user.id
    user_data[user_id]["learn_list"].pop(0)
    bot.delete_message(call.message.chat.id, call.message.message_id)
    send_next_word_to_learn(call.message.chat.id, user_id)

def ask_question(chat_id, user_id):
    data = user_data[user_id]
    if not data["quiz_list"]:
        bot.send_message(chat_id, "🏆 Tabriklayman! Barcha so'zlarni xatosiz yodlab oldingiz!")
        return

    current_word = data["quiz_list"][0]
    all_uz = [w["uz"] for w in WORDS if w["uz"] != current_word["uz"]]
    options = random.sample(all_uz, min(3, len(all_uz))) + [current_word["uz"]]
    random.shuffle(options)

    markup = InlineKeyboardMarkup()
    for opt in options:
        is_correct = "1" if opt == current_word["uz"] else "0"
        markup.add(InlineKeyboardButton(opt, callback_data=f"ans_{is_correct}"))

    bot.send_message(
        chat_id,
        f"❓ **{current_word['en']}** so'zining tarjimasi nima?",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("ans_"))
def check_answer(call):
    user_id = call.from_user.id
    data = user_data[user_id]
    is_correct = call.data.split("_")[1] == "1"
    current_word = data["quiz_list"][0]

    bot.delete_message(call.message.chat.id, call.message.message_id)

    if is_correct:
        data["quiz_list"].pop(0)
        data["learned_count"] += 1
        bot.send_message(call.message.chat.id, f"✅ To'g'ri! **{current_word['en']}** — {current_word['uz']}", parse_mode="Markdown")
        ask_question(call.message.chat.id, user_id)
    else:
        failed_word = data["quiz_list"].pop(0)
        data["quiz_list"].append(failed_word)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔄 Tushundim, davom etamiz", callback_data="retry_continue"))
        bot.send_message(
            call.message.chat.id,
            f"❌ **Xato!** Qayta yodlab oling:\n\n"
            f"🇬🇧 **{failed_word['en']}** — 🇺🇿 **{failed_word['uz']}**\n\n"
            f"_(Bu so'zni birozdan keyin yana qayta so'rayman!)_",
            reply_markup=markup,
            parse_mode="Markdown"
        )

@bot.callback_query_handler(func=lambda call: call.data == "retry_continue")
def retry_continue(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    ask_question(call.message.chat.id, call.from_user.id)

@bot.message_handler(func=lambda message: message.text == "📊 Natijam")
def show_stats(message):
    user_id = message.from_user.id
    count = user_data.get(user_id, {}).get("learned_count", 0)
    bot.send_message(message.chat.id, f"📈 Siz hozirgacha **{count}** ta so'zni muvaffaqiyatli topshirdingiz!", parse_mode="Markdown")

if __name__ == "__main__":
    print("Bot ishga tushdi...")
    bot.infinity_polling()

