# main.py
import os
import random
import logging
from fastapi import FastAPI, Request, Response
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)

# === Настройка логирования ===
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# === Токен из переменной окружения ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ Переменная окружения TELEGRAM_BOT_TOKEN не установлена!")

# === Настройка Webhook для Railway ===
# WEBHOOK_URL должен быть ПОЛНЫМ адресом, например:
# https://my-bot.up.railway.app
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_URL")  # Обязательно с https://
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "secret_key_123")
WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"

if WEBHOOK_BASE_URL:
    WEBHOOK_FULL_URL = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"
else:
    WEBHOOK_FULL_URL = None
    logger.warning("⚠️ WEBHOOK_URL не задан — вебхук не будет установлен!")

# === Шутки ===
JOKES = [
    "Мам, а правда, что люди произошли от обезьян?",
    "Как называется дата, когда программист выходит на улицу? Исключение!",
    "Программист не ошибается — он просто находит новый способ сделать задачу.",
]

# === Создаём приложение Telegram ===
application = Application.builder().token(TELEGRAM_TOKEN).build()

# === Обработчики команд ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start с кнопками"""
    keyboard = [
        [
            InlineKeyboardButton("😄 Шутка", callback_data="joke"),
            InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Что хотите?", reply_markup=reply_markup)

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /joke"""
    selected_joke = random.choice(JOKES)
    await update.message.reply_text(selected_joke)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()  # Обязательно убирает "часики" загрузки

    if query.data == "joke":
        selected_joke = random.choice(JOKES)
        await query.message.reply_text(selected_joke)
    elif query.data == "help":
        await query.message.reply_text(
            "🤖 Бот умеет:\n"
            "/start — показать меню\n"
            "/joke — рассказать шутку\n"
            "Нажимай на кнопки!"
        )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных сообщений"""
    text = update.message.text.lower()
    if "привет" in text:
        await update.message.reply_text("Привет! Попробуй /joke 😊")
    elif "как дела" in text:
        await update.message.reply_text("Отлично! А у тебя?")
    else:
        await update.message.reply_text("Я понимаю /start и /joke 😊")

# === Регистрируем обработчики ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("joke", joke))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
application.add_handler(CallbackQueryHandler(button_handler))

# === Функция установки вебхука ===
async def set_webhook():
    """Устанавливает Webhook в Telegram"""
    if not WEBHOOK_FULL_URL:
        logger.error("❌ WEBHOOK_FULL_URL не задан — пропускаю установку вебхука")
        return

    try:
        current_info = await application.bot.get_webhook_info()
        if current_info.url != WEBHOOK_FULL_URL:
            logger.info(f"🔄 Обновляю Webhook: {WEBHOOK_FULL_URL}")
            await application.bot.set_webhook(
                url=WEBHOOK_FULL_URL,
                allowed_updates=["message", "callback_query"]
            )
            logger.info("✅ Webhook успешно установлен!")
        else:
            logger.info(f"✅ Webhook уже установлен правильно: {WEBHOOK_FULL_URL}")
    except Exception as e:
        logger.error(f"❌ Ошибка при установке вебхука: {e}")

# === FastAPI приложение ===
app = FastAPI(title="Telegram Bot Webhook")

@app.on_event("startup")
async def on_startup():
    """Инициализация при запуске сервера"""
    logger.info("🚀 Запуск бота...")
    await set_webhook()
    await application.initialize()
    await application.start()
    logger.info("✅ Бот готов к работе!")

@app.on_event("shutdown")
async def on_shutdown():
    """Корректное завершение работы"""
    logger.info("🛑 Остановка бота...")
    await application.stop()
    await application.shutdown()

@app.get("/")
def health_check():
    """Эндпоинт для проверки работоспособности"""
    return {
        "status": "ok",
        "service": "telegram-bot",
        "webhook_path": WEBHOOK_PATH,
    }

@app.get("/debug")
def debug_info():
    """Эндпоинт для отладки (удалите в продакшене!)"""
    return {
        "token_set": bool(TELEGRAM_TOKEN),
        "webhook_base_url": WEBHOOK_BASE_URL,
        "webhook_full_url": WEBHOOK_FULL_URL,
    }

@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    """Обработчик входящих обновлений от Telegram"""
    try:
        json_data = await request.json()
        logger.debug(f"📩 Получено обновление: {json_data.get('update_id')}")
        update = Update.de_json(json_data, application.bot)
        await application.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {type(e).__name__} - {e}")
        return Response(status_code=500)

# Запуск для локального тестирования
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
