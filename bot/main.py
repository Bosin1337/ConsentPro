import logging
from telegram.ext import Application, CommandHandler
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из .env файла
load_dotenv()

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота из переменной окружения
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    exit(1)

async def start(update, context):
    """Обработка команды /start"""
    user = update.effective_user
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я бот для учета согласий родителей. Используйте /help для получения списка команд."
    )

async def help_command(update, context):
    """Обработка команды /help"""
    await update.message.reply_text("Список доступных команд:\n/start - Начать работу\n/help - Показать список команд")

def main():
    """Запуск бота."""
    # Создание приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Запуск бота
    logger.info("Запуск бота...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()