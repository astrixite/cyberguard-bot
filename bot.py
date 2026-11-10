# импорты
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import random
import re
import string
import ipaddress
from urllib.parse import urlsplit
import telebot
from telebot import types
from google import genai

# токен бота и клиент ИИ
TOKEN = '8702111817:AAE3swaj7G_dPgYjgY4m52oP95AzvY1xhBQ'
bot = telebot.TeleBot(TOKEN)

# Безопасная инициализация Gemini API через переменные окружения Render
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

WEBHOOK_PATH = f"/{TOKEN}"

# состояния и словари
user_states = {}
user_scores = {}

# база уязвимых паролей
COMMON_PASSWORDS = {
    '123456', 'password', '123456789', 'qwerty', '12345678',
    '12345', '1234', '111111', '1234567', 'dragon',
    '123123', 'baseball', 'football', 'monkey', 'letmein',
    'trustno1', 'admin', 'admin123', 'Admin1234', 'Password1',
    'Password123', 'qwertyuiop', 'iloveyou', 'master', 'sunshine',
    'princess', 'welcome', 'shadow', 'ashley', 'michael',
    'superman', '000000', 'abc123', 'pass123',
}

# веб-сервер и здоровье
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running with Gemini AI!")

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        if self.path == WEBHOOK_PATH:
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                json_string = post_data.decode('utf-8')
                update = telebot.types.Update.de_json(json_string)
                bot.process_new_updates([update])
                self.send_response(200)
                self.end_headers()
            except Exception as e:
                print(f"Error: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

# меню
def cg_keyboard():
    return types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("🤖 Спросить ИИ-эксперта", callback_data="cg:ai_ask")],
        [types.InlineKeyboardButton("🎣 Детектор фишинга", callback_data="cg:phishing")],
        [types.InlineKeyboardButton("🧠 Киберквиз", callback_data="cg:quiz")],
        [types.InlineKeyboardButton("🚨 Помощь при взломе", callback_data="cg:help")],
        [types.InlineKeyboardButton("🔗 Проверка ссылок", callback_data="cg:link")],
        [types.InlineKeyboardButton("📊 Рейтинг безопасности", callback_data="cg:audit")],
        [types.InlineKeyboardButton("🔑 Генератор паролей", callback_data="cg:pass_gen")],
        [types.InlineKeyboardButton("⏳ Симулятор взлома", callback_data="cg:crack_sim")],
        [types.InlineKeyboardButton("📖 Словарь киберугроз", callback_data="cg:dict")],
        [types.InlineKeyboardButton("🔗 Полезные ресурсы", callback_data="cg:tools")], # Добавили кнопку
        [types.InlineKeyboardButton("💡 Советы", callback_data="cg:tips")],
    ])

def cg_back():
    return types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="cg:menu")]
    ])

# старт
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_scores[message.chat.id] = 0
    user_states[message.chat.id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_menu = types.KeyboardButton('🛡️ Меню CyberGuard')
    btn_ai = types.KeyboardButton('🤖 Спросить ИИ-эксперта')
    btn_check = types.KeyboardButton('🛡 Аудит цифровой гигиены')
    btn_pass_gen = types.KeyboardButton('🔑 Генератор паролей')
    btn_crack_sim = types.KeyboardButton('⏳ Симулятор взлома')
    btn_dict = types.KeyboardButton('📖 Словарь киберугроз')
    btn_tools = types.KeyboardButton('🔗 Полезные ресурсы')
    btn_tips = types.KeyboardButton('💡 Советы')
    markup.add(btn_menu, btn_ai, btn_check, btn_pass_gen, btn_crack_sim, btn_dict, btn_tools, btn_tips)

    welcome_text = (
        f'Привет, {message.from_user.first_name}! 👋\n'
        'Я **CyberGuard** — твой продвинутый помощник по кибербезопасности с ИИ.\n'
        'Выбери нужную функцию в меню ниже:'
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)

# детектор фишинга
def cg_check_phishing(message_text):
    text = message_text.lower()
    warning_words = {
        "срочно": "Создаётся чувство срочности", "заблокирован": "Угроза блокировки аккаунта",
        "подтвердите": "Запрос подтверждения данных", "перейдите по ссылке": "Призыв перейти по ссылке",
        "вы выиграли": "Обещание неожиданного выигрыша", "пароль": "Упоминание пароля",
        "код подтверждения": "Запрос кода подтверждения", "urgent": "Создаётся чувство срочности",
    }
    findings = [reason for phrase, reason in warning_words.items() if phrase in text]
    if re.search(r"https?://[^\s]+", text):
        findings.append("Сообщение содержит ссылку")
    
    level = "🔴 Высокий риск" if len(findings) >= 3 else ("🟡 Есть подозрения" if len(findings) >= 1 else "🟢 Чисто")
    result = f"🎣 Анализ:\n\n{level}\n"
    if findings:
        result += "\nОбнаружено:\n" + "\n".join(f"• {item}" for item in findings)
    return result

# квиз
CG_QUIZ = [
    ("Какой пароль безопаснее?", ["12345678", "Qwerty123", "Случайный уникальный пароль"], 2, "Уникальный пароль надежнее."),
    ("Что такое фишинг?", ["Вид антивируса", "Обман для получения данных", "Обновление системы"], 1, "Фишинг — это обман."),
]

def cg_show_quiz_sync(message, context, feedback=""):
    index = context.get("cg_quiz_index", 0)
    if index >= len(CG_QUIZ):
        score = context.get("cg_quiz_score", 0)
        bot.edit_message_text(f"🏆 Квиз завершён! Результат: {score}/{len(CG_QUIZ)}", chat_id=message.chat.id, message_id=message.message_id, reply_markup=cg_back())
        return
    question, options, _, _ = CG_QUIZ[index]
    keyboard = [[types.InlineKeyboardButton(opt, callback_data=f"cg:q:{i}")] for i, opt in enumerate(options)]
    bot.edit_message_text(f"{feedback}🧠 Вопрос {index + 1}:\n\n{question}", chat_id=message.chat.id, message_id=message.message_id, reply_markup=types.InlineKeyboardMarkup(keyboard))

# помощь при взломе
CG_RECOVERY = {
    "telegram": "📱 Telegram: Настройки → Устройства → Завершить сеансы → 2FA.",
    "instagram": "📸 Instagram: instagram.com/hacked → сброс пароля.",
}

# проверка ссылок
def cg_check_link(raw):
    raw = raw.strip()
    if not raw or " " in raw: return "❌ Введи корректную ссылку."
    url = raw if "://" in raw else "https://" + raw
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    findings = []
    if parsed.scheme == "http": findings.append("Нет HTTPS")
    if "xn--" in host: findings.append("Punycode (поддельный домен)")
    return "🟡 Подозрительно:\n" + "\n".join(f"• {i}" for i in findings) if findings else "🟢 Ссылка выглядит безопасной структурой."

# аудит
CG_AUDIT = ["Используешь уникальные пароли?", "Включена ли 2FA?"]

def cg_show_audit_sync(message, context):
    index = context.get("cg_audit_index", 0)
    if index >= len(CG_AUDIT):
        score = context.get("cg_audit_score", 0) * 50
        bot.edit_message_text(f"📊 Аудит завершён! Оценка: {score}/100", chat_id=message.chat.id, message_id=message.message_id, reply_markup=cg_back())
        return
    markup = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("✅ Да", callback_data="cg:a:yes"), types.InlineKeyboardButton("❌ Нет", callback_data="cg:a:no")]])
    bot.edit_message_text(f"📊 Вопрос {index + 1}:\n\n{CG_AUDIT[index]}", chat_id=message.chat.id, message_id=message.message_id, reply_markup=markup)

# ии-консультант (Gemini)
def ask_gemini_ai(prompt):
    if not ai_client:
        return "⚠️ Ошибка: API-ключ Gemini не настроен в системе."
    try:
        response = ai_client.models.generate_content(
            model="gemini-flash-latest",
            contents=f"Ты CyberGuard — профессиональный ИИ-эксперт по кибербезопасности. Отвечай понятно, коротко и полезно. Вопрос пользователя: {prompt}",
        )
        return response.text
    except Exception as e:
        if "503" in str(e) or "UNAVAILABLE" in str(e):
            return "⚠️ Серверы Google сейчас перегружены из-за высокого спроса. Пожалуйста, повторите попытку через несколько секунд!"
        return f"⚠️ Ошибка обращения к ИИ: {e}"

# обработка кнопок
@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("cg:"))
def cg_callback(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    data = call.data
    context = user_states.setdefault(chat_id, {})

    if data == "cg:menu":
        context.pop("cg_mode", None)
        bot.edit_message_text("🛡️ Меню CyberGuard:", chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_keyboard())
    elif data == "cg:ai_ask":
        context["cg_mode"] = "waiting_for_ai"
        bot.edit_message_text("🤖 **ИИ-эксперт на связи!**\n\nЗадай мне любой вопрос по безопасности, паролям или защите аккаунтов:", chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_back(), parse_mode='Markdown')
    elif data == "cg:phishing":
        context["cg_mode"] = "phishing"
        bot.edit_message_text("🎣 Отправь текст для проверки на фишинг:", chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_back())
    elif data == "cg:link":
        context["cg_mode"] = "link"
        bot.edit_message_text("🔗 Отправь ссылку:", chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_back())
    elif data == "cg:quiz":
        context["cg_quiz_index"], context["cg_quiz_score"] = 0, 0
        cg_show_quiz_sync(call.message, context)
    elif data.startswith("cg:q:"):
        index = context.get("cg_quiz_index", 0)
        if int(data.split(":")[-1]) == CG_QUIZ[index][2]:
            context["cg_quiz_score"] = context.get("cg_quiz_score", 0) + 1
        context["cg_quiz_index"] = index + 1
        cg_show_quiz_sync(call.message, context)
    elif data == "cg:help":
        kb = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("Telegram", callback_data="cg:h:telegram")],
            [types.InlineKeyboardButton("Instagram", callback_data="cg:h:instagram")],
            [types.InlineKeyboardButton("⬅️ Меню", callback_data="cg:menu")]
        ])
        bot.edit_message_text("🚨 Где проблема?", chat_id=chat_id, message_id=call.message.message_id, reply_markup=kb)
    elif data.startswith("cg:h:"):
        bot.edit_message_text(CG_RECOVERY.get(data.split(":")[-1], "Не найдено"), chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_back())
    elif data == "cg:audit":
        context["cg_audit_index"], context["cg_audit_score"] = 0, 0
        cg_show_audit_sync(call.message, context)
    elif data.startswith("cg:a:"):
        if data == "cg:a:yes": context["cg_audit_score"] = context.get("cg_audit_score", 0) + 1
        context["cg_audit_index"] = context.get("cg_audit_index", 0) + 1
        cg_show_audit_sync(call.message, context)
    elif data == "cg:pass_gen":
        password = ''.join(random.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(14))
        bot.edit_message_text(f"🔑 Пароль:\n`{password}`", chat_id=chat_id, message_id=call.message.message_id, parse_mode='Markdown', reply_markup=cg_back())
    elif data == "cg:crack_sim":
        context["cg_mode"] = "waiting_for_crack"
        bot.edit_message_text("⏳ Введи пароль для симулятора взлома:", chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_back())
    elif data == "cg:dict":
    bot.send_message(chat_id, "📖 **Словарь киберугроз:**\n\n• **Фишинг** — выманивание данных.\n• **Брутфорс** — подбор паролей перебором.\n• **Социальная инженерия** — психологический взлом.", parse_mode='Markdown', reply_markup=cg_back())
elif data == "cg:tips":
    bot.send_message(chat_id, "💡 **Полезные советы:**\n\n1. Используйте сложные уникальные пароли.\n2. Везде включайте двухфакторную аутентификацию (2FA).\n3. Не переходите по подозрительным ссылкам.", parse_mode='Markdown', reply_markup=cg_back())

# обработка текста
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text
    context = user_states.setdefault(chat_id, {})
    state = context.get("cg_mode")

    if text == "🛡️ Меню CyberGuard":
        context.pop("cg_mode", None)
        bot.send_message(chat_id, "🛡️ Меню:", reply_markup=cg_keyboard())
        return

    # ии-режим
    if state == 'waiting_for_ai':
        bot.send_chat_action(chat_id, 'typing')
        ai_reply = ask_gemini_ai(text)
        bot.send_message(chat_id, f"🤖 **Ответ ИИ-эксперта:**\n\n{ai_reply}", parse_mode='Markdown', reply_markup=cg_back())
        return

    if state == 'waiting_for_crack':
        context["cg_mode"] = None
        pwd_len = len(text)
        time_str = "мгновенно ⚡" if pwd_len < 7 else f"около {round((70**pwd_len)/10_000_000_000, 1)} секунд ⏱"
        bot.send_message(chat_id, f"⏳ Время подбора: **{time_str}**", parse_mode='Markdown', reply_markup=cg_back())
        return

    if state == "phishing":
        context.pop("cg_mode", None)
        bot.send_message(chat_id, cg_check_phishing(text), reply_markup=cg_back())
        return

    if state == "link":
        context.pop("cg_mode", None)
        bot.send_message(chat_id, cg_check_link(text), reply_markup=cg_back())
        return

    # текстовые кнопки
    if text == '🤖 Спросить ИИ-эксперта':
        context["cg_mode"] = 'waiting_for_ai'
        bot.send_message(chat_id, "🤖 Задай свой вопрос по кибербезопасности:")
    elif text == '🔑 Генератор паролей':
        pwd = ''.join(random.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(14))
        bot.send_message(chat_id, f"🔑 Пароль:\n`{pwd}`", parse_mode='Markdown')
    elif text == '⏳ Симулятор взлома':
        context["cg_mode"] = 'waiting_for_crack'
        bot.send_message(chat_id, "⏳ Введи пароль для проверки:")
    elif text == '🛡 Аудит цифровой гигиены':
        context["cg_audit_index"], context["cg_audit_score"] = 0, 0
        markup = types.InlineKeyboardMarkup([[types.InlineKeyboardButton("✅ Да", callback_data="cg:a:yes"), types.InlineKeyboardButton("❌ Нет", callback_data="cg:a:no")]])
        bot.send_message(chat_id, f"📊 Вопрос 1:\n\n{CG_AUDIT[0]}", reply_markup=markup)
    elif text == '💡 Советы':
        bot.send_message(chat_id, "💡 Используй сложные пароли и менеджеры паролей.")

# деплой вебхука
# Замени этот финальный блок в твоем bot.py:

# деплой вебхука и запуск сервера
if __name__ == "__main__":
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if RENDER_URL:
        try:
            bot.remove_webhook()
            bot.set_webhook(url=f"{RENDER_URL}{WEBHOOK_PATH}")
            print(f"Вебхук успешно установлен на: {RENDER_URL}{WEBHOOK_PATH}")
        except Exception as e:
            print(f"Ошибка при установке вебхука: {e}")

    port = int(os.environ.get("PORT", 10000))
    print(f'Бот с Gemini ИИ успешно запущен на порту {port}!')
    HTTPServer(("0.0.0.0", port), HealthCheckHandler).serve_forever()