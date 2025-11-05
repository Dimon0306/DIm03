import telebot
import requests
import os

# Токен берётся из переменных окружения
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not API_TOKEN:
    raise ValueError("Токен не найден! Установите переменную окружения TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(API_TOKEN)

# Простые ответы на сообщения
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот, который может рассказать шутку. Напиши /joke, чтобы послушать!")

@bot.message_handler(commands=['joke'])
def send_joke(message):
    # Получаем шутку с API
    try:
        response = requests.get("https://v2.jokeapi.dev/joke/Any?safe-mode")
        data = response.json()
        if data["type"] == "single":
            joke = data["joke"]
        else:
            joke = f"{data['setup']} ... {data['delivery']}"
        bot.reply_to(message, joke)
    except Exception as e:
        bot.reply_to(message, "Не удалось получить шутку. Попробуй ещё раз!")
        print(f"Ошибка получения шутки: {e}")

# Ответ на обычные сообщения
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    text = message.text.lower()
    if 'привет' in text or 'здравствуй' in text:
        bot.reply_to(message, "Привет! Напиши /joke, чтобы услышать шутку!")
    elif 'как дела' in text:
        bot.reply_to(message, "Отлично, спасибо! А у тебя?")
    else:
        bot.reply_to(message, "Я пока не понимаю всё, но знаю много шуток! Попробуй /joke")

# Запуск бота
if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
