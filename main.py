# main.py
import os
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === Настройка логирования ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Токен из переменной окружения ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ Переменная окружения TELEGRAM_BOT_TOKEN не установлена!")

# === URL вашего бота на Render (обязательно HTTPS) ===
# Render автоматически даёт URL вида: https://<ваш-проект>.onrender.com
# Но мы получим его динамически через заголовок Host или зададим вручную
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # например: "your-bot.onrender.com"
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None

# === Создаём приложение Telegram ===
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === Обработчики команд ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот с Webhook. Напиши /joke — расскажу шутку!"
    )

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import requests
    try:
        resp = requests.get("https://v2.jokeapi.dev/joke/Any?safe-mode")
        data = resp.json()
        if data["type"] == "single":
            text = data["joke"]
        else:
            text = f"{data['setup']} ... {data['delivery']}"
        await update.message.reply_text(text)
    except Exception as e:
        logger.error(f"Ошибка получения шутки: {e}")
        await update.message.reply_text("Не удалось получить шутку. Попробуй позже.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "привет" in text:
        await update.message.reply_text("Привет! Попробуй /joke")
    elif "как дела" in text:
        await update.message.reply_text("Отлично! А у тебя?")
    else:
        await update.message.reply_text("Я понимаю /start и /joke 😊")

# Регистрируем обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("joke", joke))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# === Запуск Webhook при старте сервера ===
async def set_webhook():
    """Устанавливает Webhook в Telegram"""
    if not WEBHOOK_URL:
        logger.warning("WEBHOOK_HOST не задан — Webhook не будет установлен!")
        return

    webhook_info = await application.bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        logger.info(f"Устанавливаю Webhook: {WEBHOOK_URL}")
        await application.bot.set_webhook(url=WEBHOOK_URL)
    else:
        logger.info("Webhook уже установлен правильно.")

# === FastAPI приложение ===
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    """Вызывается при запуске сервера"""
    await set_webhook()
    # Запускаем приложение Telegram в фоне (без polling!)
    await application.initialize()
    await application.start()

@app.on_event("shutdown")
async def on_shutdown():
    """Корректное завершение"""
    await application.stop()
    await application.shutdown()

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    """Обрабатывает входящие обновления от Telegram"""
    try:
        json_data = await request.json()
        update = Update.de_json(json_data, application.bot)
        await application.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return Response(status_code=500)
