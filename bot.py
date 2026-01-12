import logging
import os  # <-- добавили
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Включим логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

JOKES = [
    "Почему программисты не ходят в лес? Боются деревьев с null-ветками!",
    "Какой язык самый грустный? JavaScript — потому что в нём всё может быть undefined.",
    "Зачем AI пошёл к психологу? У него был deep learning... но не deep feeling."
]

joke_index = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Привет, {user.first_name}! 👋\n"
        "Че кого!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "шутка" in text or "анекдот" in text or "joke" in text:
        global joke_index
        joke = JOKES[joke_index]
        joke_index = (joke_index + 1) % len(JOKES)
        await update.message.reply_text(joke)
    else:
        await update.message.reply_text("Интересно! А теперь скажи «шутка» 😉")

def main():
    # 🔒 Получаем токен из переменной окружения
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("❌ Переменная окружения TELEGRAM_BOT_TOKEN не установлена!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Бот запущен и готов к работе!")
    app.run_polling()

if __name__ == "__main__":
    main()
