import random
import re
import string
import telebot
from telebot import types

# Вставьте сюда токен вашего бота от @BotFather
TOKEN = '8702111817:AAE3swaj7G_dPgYjgY4m52oP95AzvY1xhBQ'
bot = telebot.TeleBot(TOKEN)

# Словари для отслеживания состояний пользователей
user_states = {}
user_scores = {}

# Большой черный список популярных и уязвимых паролей (для умного симулятора)
COMMON_PASSWORDS = {
    '123456',
    'password',
    '123456789',
    'qwerty',
    '12345678',
    '12345',
    '1234',
    '111111',
    '1234567',
    'dragon',
    '123123',
    'baseball',
    'football',
    'monkey',
    'letmein',
    'trustno1',
    'admin',
    'admin123',
    'Admin1234',
    'Password1',
    'Password123',
    'qwertyuiop',
    'iloveyou',
    'master',
    'sunshine',
    'princess',
    'welcome',
    'shadow',
    'ashley',
    'michael',
    'superman',
    'trustno1',
    '000000',
    'abc123',
    'pass123',
}


# Обработка команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
  user_scores[message.chat.id] = 0
  user_states[message.chat.id] = None

  markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
  btn_check = types.KeyboardButton('🛡 Аудит цифровой гигиены')
  btn_pass_gen = types.KeyboardButton('🔑 Генератор паролей')
  btn_crack_sim = types.KeyboardButton('⏳ Симулятор взлома')
  btn_dict = types.KeyboardButton('📖 Словарь киберугроз')
  btn_tools = types.KeyboardButton('🔗 Полезные ресурсы')
  btn_tips = types.KeyboardButton('💡 Советы')
  markup.add(
      btn_check, btn_pass_gen, btn_crack_sim, btn_dict, btn_tools, btn_tips
  )

  welcome_text = (
      f'Привет, {message.from_user.first_name}! 👋\n'
      'Я **CyberGuard** — твой продвинутый помощник по кибербезопасности.\n'
      'Выбери нужную функцию в меню ниже:'
  )
  bot.send_message(
      message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=markup
  )


# Обработка текстовых кнопок меню
@bot.message_handler(func=lambda message: True)
def handle_message(message):
  chat_id = message.chat.id
  text = message.text

  # Проверка состояния ожидания пароля для симулятора взлома
  if user_states.get(chat_id) == 'waiting_for_crack_password':
    password = message.text
    user_states[chat_id] = None
    simulate_crack_time(chat_id, password)
    return

  # 1. Генератор паролей
  if text == '🔑 Генератор паролей':
    chars = string.ascii_letters + string.digits + '!@#$%^&*'
    password = ''.join(random.choice(chars) for _ in range(14))
    gen_text = (
        '🔑 **Генератор безопасных паролей**\n\n'
        f'Вот надежный случайный пароль для тебя:\n`{password}`\n\n'
        '*(Используй его для новых аккаунтов и никому не показывай!)*'
    )
    bot.send_message(chat_id, gen_text, parse_mode='Markdown')
    return

  # 3. Словарь киберугроз
  elif text == '📖 Словарь киберугроз':
    dict_text = (
        '📖 **Словарь киберугроз и терминов:**\n\n'
        '1️⃣ **Фишинг (Phishing)** — вид мошенничества, когда злоумышленники притворяются '
        'компаниями (банками, соцсетями), чтобы украсть твои пароли.\n\n'
        '2️⃣ **Брутфорс (Brute-force)** — метод подбора паролей перебором всех возможных '
        'комбинаций с помощью компьютера.\n\n'
        '3️⃣ **Вредоносное ПО (Malware)** — программы, созданные для кражи данных, '
        'блокировки системы или шпионажа (вирусы, трояны, шифровальщики).\n\n'
        '4️⃣ **Социальная инженерия** — психологический взлом людей (манипуляции, обман), '
        'чтобы жертва сама отдала пароль или перевела деньги.'
    )
    bot.send_message(chat_id, dict_text, parse_mode='Markdown')
    return

  # 5. Симулятор времени взлома пароля
  elif text == '⏳ Симулятор взлома':
    user_states[chat_id] = 'waiting_for_crack_password'
    bot.send_message(
        chat_id,
        '⏳ **Симулятор взлома (Интеллектуальный анализ)**\n\n'
        'Введи любой пароль в чат, и наша система проверит его по базам утекших '
        'паролей и рассчитает время брутфорс-подбора.\n'
        '*(Совет: в целях безопасности не вводи свои реальные пароли!)*',
        parse_mode='Markdown',
    )
    return

  # Аудит цифровой гигиены (чек-лист)
  if text == '🛡 Аудит цифровой гигиены':
    user_scores[chat_id] = 0
    send_question_1(chat_id)

  # Полезные ресурсы
  elif text == '🔗 Полезные ресурсы':
    tools_text = (
        '🔗 **Полезные ресурсы для кибербезопасности:**\n\n'
        '1. **Проверка утечек:** [Have I Been Pwned](https://haveibeenpwned.com/)\n'
        '2. **Менеджеры паролей:** [Bitwarden](https://bitwarden.com/)\n'
        '3. **Стандарты:** [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)'
    )
    bot.send_message(
        chat_id,
        tools_text,
        parse_mode='Markdown',
        disable_web_page_preview=True,
    )

  # Советы
  elif text == '💡 Советы':
    tips = (
        '📌 **Топ-3 правила цифровой гигиены:**\n\n'
        '1. Никогда не используй одинаковые пароли.\n'
        '2. Включай двухфакторную аутентификацию (2FA).\n'
        '3. Не переходи по сомнительным ссылкам.'
    )
    bot.send_message(chat_id, tips, parse_mode='Markdown')


# Интеллектуальная логика симулятора времени взлома
def simulate_crack_time(chat_id, password):
  # Сначала проверяем по словарю популярных/утекших паролей
  if password in COMMON_PASSWORDS or password.lower() in COMMON_PASSWORDS:
    result_msg = (
        '⏳ **Результаты симулятора взлома:**\n\n'
        f'Длина пароля: **{len(password)} симв.**\n'
        '⚠️ **ВНИМАНИЕ! Этот пароль найден в глобальном списке самых популярных и утекших паролей мира!**\n'
        'Время подбора брутфорс/словарным методом: **Менее 0.001 секунды (Взломан мгновенно!)** 🚨\n\n'
        '*(Хакеры проверяют такие пароли в первую очередь. Срочно замените его!)*'
    )
    bot.send_message(chat_id, result_msg, parse_mode='Markdown')
    return

  # Если пароля нет в словаре — считаем математическую сложность
  length = len(password)
  has_lower = bool(re.search(r'[a-z]', password))
  has_upper = bool(re.search(r'[A-Z]', password))
  has_digit = bool(re.search(r'\d', password))
  has_symbol = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

  charset_size = 0
  if has_lower:
    charset_size += 26
  if has_upper:
    charset_size += 26
  if has_digit:
    charset_size += 10
  if has_symbol:
    charset_size += 32

  if charset_size == 0:
    charset_size = 10

  combinations = charset_size**length
  seconds = combinations / 10_000_000_000  # 10 млрд комбинаций в секунду

  if seconds < 0.001:
    time_str = 'меньше одной миллисекунды (мгновенно!) ⚡'
  elif seconds < 60:
    time_str = f'около {round(seconds, 2)} секунд ⏱'
  elif seconds < 3600:
    time_str = f'около {round(seconds / 60, 1)} минут ⏳'
  elif seconds < 86400:
    time_str = f'около {round(seconds / 3600, 1)} часов 🕒'
  elif seconds < 31536000:
    time_str = f'около {round(seconds / 86400, 1)} дней 📅'
  elif seconds < 31536000 * 1000:
    time_str = f'около {round(seconds / 31536000, 1)} лет 🛡'
  else:
    time_str = 'сотни или тысячи лет (абсолютно надежно!) 🚀'

  result_msg = (
      '⏳ **Результаты симулятора взлома:**\n\n'
      f'Длина пароля: **{length} симв.**\n'
      f'Время подбора брутфорс-ботом: **{time_str}**'
  )
  bot.send_message(chat_id, result_msg, parse_mode='Markdown')


# --- БЛОК ЧЕК-ЛИСТА (5 ВОПРОСОВ) ---
def send_question_1(chat_id):
  markup = types.InlineKeyboardMarkup()
  markup.add(
      types.InlineKeyboardButton('🟢 Да', callback_data='q1_yes'),
      types.InlineKeyboardButton('🔴 Нет', callback_data='q1_no'),
  )
  bot.send_message(
      chat_id,
      '❓ **Вопрос 1 из 5:**\nИспользуешь ли ты двухфакторную аутентификацию'
      ' (2FA) в соцсетях и почте?',
      parse_mode='Markdown',
      reply_markup=markup,
  )


def send_question_2(chat_id):
  markup = types.InlineKeyboardMarkup()
  markup.add(
      types.InlineKeyboardButton('🟢 Да', callback_data='q2_yes'),
      types.InlineKeyboardButton('🔴 Нет', callback_data='q2_no'),
  )
  bot.send_message(
      chat_id,
      '❓ **Вопрос 2 из 5:**\nСоздаешь ли ты уникальные и сложные пароли для'
      ' каждого нового сайта?',
      parse_mode='Markdown',
      reply_markup=markup,
  )


def send_question_3(chat_id):
  markup = types.InlineKeyboardMarkup()
  markup.add(
      types.InlineKeyboardButton('🟢 Да', callback_data='q3_yes'),
      types.InlineKeyboardButton('🔴 Нет', callback_data='q3_no'),
  )
  bot.send_message(
      chat_id,
      '❓ **Вопрос 3 из 5:**\nРегулярно ли ты делаешь резервные копии (бэкапы)'
      ' важных файлов?',
      parse_mode='Markdown',
      reply_markup=markup,
  )


def send_question_4(chat_id):
  markup = types.InlineKeyboardMarkup()
  markup.add(
      types.InlineKeyboardButton('🟢 Да', callback_data='q4_yes'),
      types.InlineKeyboardButton('🔴 Нет', callback_data='q4_no'),
  )
  bot.send_message(
      chat_id,
      '❓ **Вопрос 4 из 5:**\nПользуешься ли ты официальными менеджерами паролей'
      ' вместо записочек и заметок?',
      parse_mode='Markdown',
      reply_markup=markup,
  )


def send_question_5(chat_id):
  markup = types.InlineKeyboardMarkup()
  markup.add(
      types.InlineKeyboardButton('🟢 Да', callback_data='q5_yes'),
      types.InlineKeyboardButton('🔴 Нет', callback_data='q5_no'),
  )
  bot.send_message(
      chat_id,
      '❓ **Вопрос 5 из 5:**\nПроверяешь ли ты адрес ссылки (домен) перед тем,'
      ' как вводить свои данные?',
      parse_mode='Markdown',
      reply_markup=markup,
  )


# Обработка ответов на чек-лист
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
  chat_id = call.message.chat.id
  if chat_id not in user_scores:
    user_scores[chat_id] = 0

  if call.data == 'q1_yes':
    user_scores[chat_id] += 1
    bot.answer_callback_query(call.id, 'Верно!')
    bot.edit_message_text(
        '✅ Вопрос 1: Двухфакторная защита включена (+1 балл)',
        chat_id,
        call.message.message_id,
    )
    send_question_2(chat_id)
  elif call.data == 'q1_no':
    bot.answer_callback_query(call.id, 'Рискованно!')
    bot.edit_message_text(
        '⚠️ Вопрос 1: Без 2FA аккаунты уязвимы для взлома.',
        chat_id,
        call.message.message_id,
    )
    send_question_2(chat_id)

  elif call.data == 'q2_yes':
    user_scores[chat_id] += 1
    bot.answer_callback_query(call.id, 'Отлично!')
    bot.edit_message_text(
        '✅ Вопрос 2: Уникальные пароли — залог безопасности (+1 балл)',
        chat_id,
        call.message.message_id,
    )
    send_question_3(chat_id)
  elif call.data == 'q2_no':
    bot.answer_callback_query(call.id, 'Опасно!')
    bot.edit_message_text(
        '⚠️ Вопрос 2: Использование одного пароля везде ведет к взлому.',
        chat_id,
        call.message.message_id,
    )
    send_question_3(chat_id)

  elif call.data == 'q3_yes':
    user_scores[chat_id] += 1
    bot.answer_callback_query(call.id, 'Супер!')
    bot.edit_message_text(
        '✅ Вопрос 3: Резервные копии защищают от потери данных (+1 балл)',
        chat_id,
        call.message.message_id,
    )
    send_question_4(chat_id)
  elif call.data == 'q3_no':
    bot.answer_callback_query(call.id, 'Внимание!')
    bot.edit_message_text(
        '⚠️ Вопрос 3: Без бэкапов можно навсегда потерять файлы.',
        chat_id,
        call.message.message_id,
    )
    send_question_4(chat_id)

  elif call.data == 'q4_yes':
    user_scores[chat_id] += 1
    bot.answer_callback_query(call.id, 'Правильно!')
    bot.edit_message_text(
        '✅ Вопрос 4: Менеджер паролей защищает твои данные (+1 балл)',
        chat_id,
        call.message.message_id,
    )
    send_question_5(chat_id)
  elif call.data == 'q4_no':
    bot.answer_callback_query(call.id, 'Советуем начать!')
    bot.edit_message_text(
        '⚠️ Вопрос 4: Хранить пароли в заметках небезопасно.',
        chat_id,
        call.message.message_id,
    )
    send_question_5(chat_id)

  elif call.data == 'q5_yes':
    user_scores[chat_id] += 1
    bot.answer_callback_query(call.id, 'Отлично!')
    bot.edit_message_text(
        '✅ Вопрос 5: Внимательность к ссылкам защищает от фишинга (+1 балл)',
        chat_id,
        call.message.message_id,
    )
    show_final_result(chat_id)
  elif call.data == 'q5_no':
    bot.answer_callback_query(call.id, 'Осторожнее!')
    bot.edit_message_text(
        '⚠️ Вопрос 5: Из-за невнимательности к ссылкам попадаются на уловки.',
        chat_id,
        call.message.message_id,
    )
    show_final_result(chat_id)


def show_final_result(chat_id):
  score = user_scores.get(chat_id, 0)
  result_text = f'🏁 **Аудит завершен! Твой результат: {score} из 5 баллов.**\n\n'

  if score == 5:
    result_text += '🎉 **Идеально!** У тебя отличный уровень цифровой гигиены.'
  elif score >= 3:
    result_text += (
        '⚠️ **Неплохо, но есть слабые места.** Стоит улучшить привычки.'
    )
  else:
    result_text += (
        '🚨 **Высокий риск!** Твои данные уязвимы для киберпреступников.'
    )

  bot.send_message(chat_id, result_text, parse_mode='Markdown')


# Запуск бота
print('Умный бот с защитой от популярных паролей запущен!')
bot.polling(none_stop=True)