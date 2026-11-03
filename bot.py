import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import random
import re
import string
import ipaddress
from urllib.parse import urlsplit
import telebot
from telebot import types

# ТОКЕН ВАШЕГО БОТА ОТ @BotFather
TOKEN = '8702111817:AAE3swaj7G_dPgYjgY4m52oP95AzvY1xhBQ'
bot = telebot.TeleBot(TOKEN)

# Безопасный путь для вебхука на основе токена
WEBHOOK_PATH = f"/{TOKEN}"

# Словари для отслеживания состояний пользователей
user_states = {}
user_scores = {}

# Большой черный список популярных и уязвимых паролей
COMMON_PASSWORDS = {
    '123456', 'password', '123456789', 'qwerty', '12345678',
    '12345', '1234', '111111', '1234567', 'dragon',
    '123123', 'baseball', 'football', 'monkey', 'letmein',
    'trustno1', 'admin', 'admin123', 'Admin1234', 'Password1',
    'Password123', 'qwertyuiop', 'iloveyou', 'master', 'sunshine',
    'princess', 'welcome', 'shadow', 'ashley', 'michael',
    'superman', '000000', 'abc123', 'pass123',
}


# Мини-сервер для обработки вебхуков от Telegram и пингов от Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive and running on Webhooks!")

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        if self.path == WEBHOOK_PATH:
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                json_string = post_data.decode('utf-8')
                
                # Передаем обновление боту
                update = telebot.types.Update.de_json(json_string)
                bot.process_new_updates([update])
                
                self.send_response(200)
                self.end_headers()
            except Exception as e:
                print(f"Error processing update: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    print(f"Web server started on port {port}")
    server.serve_forever()


# Запускаем веб-сервер в фоновом потоке
threading.Thread(target=run_web_server, daemon=True).start()


# ========== МЕНЮ КИБЕРГУРД (Инлайн) ==========

def cg_keyboard():
    return types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("🎣 Детектор фишинга", callback_data="cg:phishing")],
        [types.InlineKeyboardButton("🧠 Киберквиз", callback_data="cg:quiz")],
        [types.InlineKeyboardButton("🚨 Помощь при взломе", callback_data="cg:help")],
        [types.InlineKeyboardButton("🔗 Проверка ссылок", callback_data="cg:link")],
        [types.InlineKeyboardButton("📊 Рейтинг безопасности", callback_data="cg:audit")],
        [types.InlineKeyboardButton("🔑 Генератор паролей", callback_data="cg:pass_gen")],
        [types.InlineKeyboardButton("⏳ Симулятор взлома", callback_data="cg:crack_sim")],
        [types.InlineKeyboardButton("📖 Словарь киберугроз", callback_data="cg:dict")],
        [types.InlineKeyboardButton("💡 Советы", callback_data="cg:tips")],
    ])

def cg_back():
    return types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("⬅️ Назад в меню", callback_data="cg:menu")]
    ])


# Обработка команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_scores[message.chat.id] = 0
    user_states[message.chat.id] = {}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_menu = types.KeyboardButton('🛡️ Меню CyberGuard')
    btn_check = types.KeyboardButton('🛡 Аудит цифровой гигиены')
    btn_pass_gen = types.KeyboardButton('🔑 Генератор паролей')
    btn_crack_sim = types.KeyboardButton('⏳ Симулятор взлома')
    btn_dict = types.KeyboardButton('📖 Словарь киберугроз')
    btn_tools = types.KeyboardButton('🔗 Полезные ресурсы')
    btn_tips = types.KeyboardButton('💡 Советы')
    markup.add(btn_menu, btn_check, btn_pass_gen, btn_crack_sim, btn_dict, btn_tools, btn_tips)

    welcome_text = (
        f'Привет, {message.from_user.first_name}! 👋\n'
        'Я **CyberGuard** — твой продвинутый помощник по кибербезопасности.\n'
        'Выбери нужную функцию в меню ниже:'
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup)


# ========== 1. ДЕТЕКТОР ФИШИНГА ==========

def cg_check_phishing(message_text):
    text = message_text.lower()
    warning_words = {
        "срочно": "Создаётся чувство срочности",
        "заблокирован": "Угроза блокировки аккаунта",
        "подтвердите": "Запрос подтверждения данных",
        "перейдите по ссылке": "Призыв перейти по ссылке",
        "вы выиграли": "Обещание неожиданного выигрыша",
        "пароль": "Упоминание пароля",
        "код подтверждения": "Запрос кода подтверждения",
        "никому не сообщайте": "Манипуляция конфиденциальностью",
        "urgent": "Создаётся чувство срочности",
        "verify your account": "Запрос подтверждения аккаунта",
        "click here": "Призыв перейти по ссылке",
        "otp": "Упоминание одноразового кода",
    }
    findings = []
    for phrase, reason in warning_words.items():
        if phrase in text and reason not in findings:
            findings.append(reason)
    if re.search(r"https?://[^\s]+", text):
        findings.append("Сообщение содержит ссылку")

    if len(findings) >= 3:
        level = "🔴 Высокий уровень подозрительности"
    elif len(findings) >= 1:
        level = "🟡 Есть подозрительные признаки"
    else:
        level = "🟢 Явных признаков не найдено"

    result = f"🎣 Результат анализа:\n\n{level}\n"
    if findings:
        result += "\nОбнаружено:\n" + "\n".join(f"• {item}" for item in findings)
    result += (
        "\n\n💡 Не переходи по неизвестным ссылкам, не передавай коды и пароли."
        "\n\n⚠️ Это предварительный анализ, а не гарантия безопасности сообщения."
    )
    return result


# ========== 2. КИБЕРКВИЗ ==========

CG_QUIZ = [
    ("Какой пароль безопаснее?", ["12345678", "Qwerty123", "Случайный уникальный пароль"], 2, "Уникальный случайный пароль сложнее угадать."),
    ("Что такое фишинг?", ["Вид антивируса", "Обман для получения данных", "Обновление системы"], 1, "Фишинг используется для обмана и кражи информации."),
    ("Что делать с подозрительной ссылкой?", ["Сразу открыть", "Переслать друзьям", "Проверить отправителя и адрес"], 2, "Не открывай сомнительные ссылки без проверки."),
    ("Для чего нужна двухфакторная аутентификация?", ["Для ускорения интернета", "Для дополнительной защиты", "Для удаления вирусов"], 1, "Второй фактор усложняет захват аккаунта."),
    ("Что делать при подозрении на взлом?", ["Ничего", "Сменить пароль и завершить чужие сеансы", "Удалить все приложения"], 1, "Нужно восстановить контроль и защитить аккаунт."),
]

def cg_show_quiz_sync(message, context, feedback=""):
    index = context.get("cg_quiz_index", 0)
    if index >= len(CG_QUIZ):
        score = context.get("cg_quiz_score", 0)
        bot.edit_message_text(
            f"🏆 Квиз завершён!\n\nТвой результат: {score}/{len(CG_QUIZ)}\n\n"
            f"{'Отлично!' if score == len(CG_QUIZ) else 'Продолжай изучать кибербезопасность!'}",
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=cg_back()
        )
        return

    question, options, _, _ = CG_QUIZ[index]
    keyboard = [[types.InlineKeyboardButton(opt, callback_data=f"cg:q:{i}")] for i, opt in enumerate(options)]
    text = f"{feedback}🧠 Вопрос {index + 1}/{len(CG_QUIZ)}\n\n{question}"
    bot.edit_message_text(text, chat_id=message.chat.id, message_id=message.message_id, reply_markup=types.InlineKeyboardMarkup(keyboard))


# ========== 3. ПОМОЩЬ ПРИ ВЗЛОМЕ ==========

CG_RECOVERY = {
    "telegram": (
        "📱 Если взломали Telegram:\n\n1. Открой Настройки → Устройства.\n2. Заверши все незнакомые сеансы.\n"
        "3. Включи двухэтапную проверку.\n4. Проверь безопасность номера телефона.\n5. Предупреди знакомых о подозрительных сообщениях."
    ),
    "instagram": (
        "📸 Если взломали Instagram:\n\n1. Открой instagram.com/hacked.\n2. Начни восстановление аккаунта.\n"
        "3. Смени пароль, если доступ сохранился.\n4. Заверши незнакомые сеансы.\n5. Включи двухфакторную аутентификацию."
    ),
    "google": (
        "📧 Если взломали Google:\n\n1. Открой accounts.google.com/signin/recovery.\n2. Восстанови доступ.\n"
        "3. Смени пароль.\n4. Проверь подключённые устройства.\n5. Включи двухэтапную проверку."
    ),
    "link": (
        "🔗 Если перешёл по подозрительной ссылке:\n\n1. Не вводи личные данные.\n2. Закрой подозрительный сайт.\n"
        "3. Если вводил пароль — смени его.\n4. Если загрузил файл — не открывай.\n5. Проверь активные сеансы и включи 2FA."
    ),
}


# ========== 4. ПРОВЕРКА ССЫЛОК ==========

def cg_check_link(raw):
    raw = raw.strip()
    if not raw or re.search(r"\s", raw):
        return "❌ Введи один корректный адрес сайта."
    url = raw if "://" in raw else "https://" + raw
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in ("http", "https") or not host:
            return "❌ Поддерживаются только HTTP и HTTPS ссылки."
        if "." not in host and host != "localhost":
            return "❌ Некорректное доменное имя."
    except ValueError:
        return "❌ Не удалось распознать ссылку."

    findings = []
    if parsed.scheme == "http":
        findings.append("Соединение не использует HTTPS")
    if parsed.username or parsed.password or "@" in parsed.netloc:
        findings.append("В адресе присутствует символ @")
    if "xn--" in host:
        findings.append("Домен содержит Punycode — проверь написание")
    try:
        ipaddress.ip_address(host)
        findings.append("Вместо домена используется IP-адрес")
    except ValueError:
        pass
    shorteners = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "tiny.cc")
    if host in shorteners or any(host.endswith("." + s) for s in shorteners):
        findings.append("Используется сокращатель ссылок")
    if host.count(".") >= 4:
        findings.append("В домене много поддоменов")
    if len(host) > 65:
        findings.append("Необычно длинное доменное имя")

    if findings:
        result = "🟡 Обнаружены признаки, требующие проверки:\n\n" + "\n".join(f"• {item}" for item in findings)
    else:
        result = "🟢 Очевидных подозрительных признаков не обнаружено."
    result += "\n\n⚠️ Бот проверил только структуру адреса, не открывая сайт."
    return result


# ========== 5. РЕЙТИНГ БЕЗОПАСНОСТИ ==========

CG_AUDIT = [
    "Используешь уникальные пароли для разных аккаунтов?",
    "Включена ли двухфакторная аутентификация?",
    "Регулярно обновляешь приложения и систему?",
    "Проверяешь ссылки перед переходом?",
    "Есть ли резервные копии важных данных?",
]

def cg_show_audit_sync(message, context):
    index = context.get("cg_audit_index", 0)
    if index >= len(CG_AUDIT):
        score = context.get("cg_audit_score", 0) * 20
        if score >= 80: level = "🟢 Хорошие привычки безопасности"
        elif score >= 60: level = "🟡 Есть что улучшить"
        else: level = "🔴 Стоит усилить защиту"
        bot.edit_message_text(
            f"📊 Рейтинг безопасности\n\nРезультат: {score}/100\n{level}\n\nЭто учебный показатель.",
            chat_id=message.chat.id,
            message_id=message.message_id,
            reply_markup=cg_back()
        )
        return

    keyboard = types.InlineKeyboardMarkup([
        [
            types.InlineKeyboardButton("✅ Да", callback_data="cg:a:yes"),
            types.InlineKeyboardButton("❌ Нет", callback_data="cg:a:no")
        ]
    ])
    bot.edit_message_text(f"📊 Вопрос {index + 1}/{len(CG_AUDIT)}\n\n{CG_AUDIT[index]}", chat_id=message.chat.id, message_id=message.message_id, reply_markup=keyboard)


# ========== ОБРАБОТКА ИНЛАЙН-КНОПОК (CALLBACK) ==========

@bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("cg:"))
def cg_callback(call):
    bot.answer_callback_query(call.id)
    chat_id = call.message.chat.id
    data = call.data

    if chat_id not in user_states:
        user_states[chat_id] = {}
    context = user_states[chat_id]

    if data == "cg:menu":
        context.pop("cg_mode", None)
        bot.edit_message_text("🛡️ CyberGuard Bot\n\nВыбери инструмент безопасности:", chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_keyboard())

    elif data == "cg:phishing":
        context["cg_mode"] = "phishing"
        bot.edit_message_text("🎣 Отправь текст подозрительного сообщения.\n\nУдали личные данные перед отправкой.", chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_back())

    elif data == "cg:link":
        context["cg_mode"] = "link"
        bot.edit_message_text("🔗 Отправь ссылку, которую хочешь проверить.", chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_back())

    elif data == "cg:quiz":
        context.pop("cg_mode", None)
        context["cg_quiz_index"] = 0
        context["cg_quiz_score"] = 0
        cg_show_quiz_sync(call.message, context)

    elif data.startswith("cg:q:"):
        index = context.get("cg_quiz_index", 0)
        answer = int(data.split(":")[-1])
        _, _, correct, explanation = CG_QUIZ[index]
        feedback = "✅ Правильно!\n" if answer == correct else "❌ Неправильно.\n"
        if answer == correct:
            context["cg_quiz_score"] = context.get("cg_quiz_score", 0) + 1
        context["cg_quiz_index"] = index + 1
        cg_show_quiz_sync(call.message, context, feedback + explanation + "\n\n")

    elif data == "cg:help":
        keyboard = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("Telegram", callback_data="cg:h:telegram")],
            [types.InlineKeyboardButton("Instagram", callback_data="cg:h:instagram")],
            [types.InlineKeyboardButton("Google", callback_data="cg:h:google")],
            [types.InlineKeyboardButton("Подозрительная ссылка", callback_data="cg:h:link")],
            [types.InlineKeyboardButton("⬅️ Назад", callback_data="cg:menu")]
        ])
        bot.edit_message_text("🚨 Выбери проблему:", chat_id=chat_id, message_id=call.message.message_id, reply_markup=keyboard)

    elif data.startswith("cg:h:"):
        service = data.split(":")[-1]
        bot.edit_message_text(CG_RECOVERY.get(service, "Сценарий не найден."), chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_back())

    elif data == "cg:audit":
        context.pop("cg_mode", None)
        context["cg_audit_index"] = 0
        context["cg_audit_score"] = 0
        cg_show_audit_sync(call.message, context)

    elif data.startswith("cg:a:"):
        if "cg_audit_index" in context:
            if data == "cg:a:yes":
                context["cg_audit_score"] = context.get("cg_audit_score", 0) + 1
            context["cg_audit_index"] = context.get("cg_audit_index", 0) + 1
            cg_show_audit_sync(call.message, context)

    elif data == "cg:pass_gen":
        chars = string.ascii_letters + string.digits + '!@#$%^&*'
        password = ''.join(random.choice(chars) for _ in range(14))
        gen_text = f'🔑 **Генератор безопасных паролей**\n\nВот надежный пароль:\n`{password}`'
        bot.edit_message_text(gen_text, chat_id=chat_id, message_id=call.message.message_id, parse_mode='Markdown', reply_markup=cg_back())

    elif data == "cg:crack_sim":
        context["cg_mode"] = "waiting_for_crack_password"
        bot.edit_message_text('⏳ **Симулятор взлома**\n\nВведи пароль в чат для проверки на уязвимость:', chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_back())

    elif data == "cg:dict":
        dict_text = (
            '📖 **Словарь киберугроз:**\n\n'
            '1️⃣ **Фишинг** — кража данных обманом.\n'
            '2️⃣ **Брутфорс** — подбор паролей перебором.\n'
            '3️⃣ **Вредоносное ПО** — вирусы и трояны.\n'
            '4️⃣ **Социальная инженерия** — психологический взлом.'
        )
        bot.edit_message_text(dict_text, chat_id=chat_id, message_id=call.message.message_id, parse_mode='Markdown', reply_markup=cg_back())

    elif data == "cg:tips":
        tips = '📌 **Советы:**\n1. Используй разные пароли.\n2. Включи 2FA.\n3. Не переходи по подозрительным ссылкам.'
        bot.edit_message_text(tips, chat_id=chat_id, message_id=call.message.message_id, reply_markup=cg_back())


# ========== ОБРАБОТКА ТЕКСТА И КНОПОК НИЖНЕГО МЕНЮ ==========

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    if chat_id not in user_states:
        user_states[chat_id] = {}
    
    state = user_states[chat_id].get("cg_mode")

    if text == "🛡️ Меню CyberGuard":
        user_states[chat_id].pop("cg_mode", None)
        bot.send_message(chat_id, "🛡️ CyberGuard Bot\n\nВыбери инструмент безопасности:", reply_markup=cg_keyboard())
        return

    if state == 'waiting_for_crack_password':
        user_states[chat_id]["cg_mode"] = None
        simulate_crack_time_local(chat_id, text)
        return

    if state == "phishing":
        result = cg_check_phishing(text)
        user_states[chat_id].pop("cg_mode", None)
        bot.send_message(chat_id, result, reply_markup=cg_back(), parse_mode='Markdown')
        return

    if state == "link":
        result = cg_check_link(text)
        user_states[chat_id].pop("cg_mode", None)
        bot.send_message(chat_id, result, reply_markup=cg_back())
        return

    if text == '🔑 Генератор паролей':
        chars = string.ascii_letters + string.digits + '!@#$%^&*'
        password = ''.join(random.choice(chars) for _ in range(14))
        bot.send_message(chat_id, f'🔑 **Генератор паролей**\n\n`{password}`', parse_mode='Markdown')
    elif text == '📖 Словарь киберугроз':
        dict_text = (
            '📖 **Словарь киберугроз:**\n\n'
            '1️⃣ **Фишинг** — кража данных обманом.\n'
            '2️⃣ **Брутфорс** — подбор паролей перебором.\n'
            '3️⃣ **Вредоносное ПО** — вирусы и трояны.\n'
            '4️⃣ **Социальная инженерия** — психологический взлом.'
        )
        bot.send_message(chat_id, dict_text, parse_mode='Markdown')
    elif text == '⏳ Симулятор взлома':
        user_states[chat_id]["cg_mode"] = 'waiting_for_crack_password'
        bot.send_message(chat_id, '⏳ Введи пароль для проверки времени подбора:')
    elif text == '🛡 Аудит цифровой гигиены':
        user_scores[chat_id] = 0
        user_states[chat_id]["cg_audit_index"] = 0
        user_states[chat_id]["cg_audit_score"] = 0
        markup = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton("🟢 Да", callback_data="cg:a:yes"), types.InlineKeyboardButton("🔴 Нет", callback_data="cg:a:no")]
        ])
        bot.send_message(chat_id, f'📊 Вопрос 1/5:\n\n{CG_AUDIT[0]}', reply_markup=markup)
    elif text == '🔗 Полезные ресурсы':
        tools_text = (
            '🔗 **Полезные ресурсы:**\n\n'
            '1. **Проверка утечек:** [Have I Been Pwned](https://haveibeenpwned.com/)\n'
            '2. **Менеджеры паролей:** [Bitwarden](https://bitwarden.com/)'
        )
        bot.send_message(chat_id, tools_text, parse_mode='Markdown', disable_web_page_preview=True)
    elif text == '💡 Советы':
        tips = '📌 **Топ-3 правила цифровой гигиены:**\n\n1. Никогда не используй одинаковые пароли.\n2. Включай двухфакторную аутентификацию (2FA).\n3. Не переходи по сомнительным ссылкам.'
        bot.send_message(chat_id, tips, parse_mode='Markdown')


def simulate_crack_time_local(chat_id, password):
    if password in COMMON_PASSWORDS or password.lower() in COMMON_PASSWORDS:
        bot.send_message(chat_id, '⏳ **Результаты симулятора взлома:**\n\n⚠️ Этот пароль найден в базе утечек! Взломан мгновенно 🚨', parse_mode='Markdown')
        return
    length = len(password)
    combinations = 70 ** length
    seconds = combinations / 10_000_000_000
    if seconds < 1: time_str = "мгновенно ⚡"
    else: time_str = f"около {round(seconds, 1)} секунд ⏱"
    bot.send_message(chat_id, f'⏳ **Результаты симулятора взлома:**\n\nВремя подбора брутфорс-ботом: **{time_str}**', parse_mode='Markdown')


# Установка вебхука при старте приложения
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")
if RENDER_URL:
    webhook_url = f"{RENDER_URL}{WEBHOOK_PATH}"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print(f"Webhook successfully set to: {webhook_url}")
else:
    print("WARNING: RENDER_EXTERNAL_URL not found.")

print('Умный бот CyberGuard успешно запущен на вебхуках!')