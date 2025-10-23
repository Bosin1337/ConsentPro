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

# Импортируем обработчики
from handlers.start import start

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
    application.add_handler(CommandHandler("add_teacher", add_teacher))
    application.add_handler(CommandHandler("remove_teacher", remove_teacher))
    application.add_handler(CommandHandler("add_class", add_class))
    application.add_handler(CommandHandler("my_classes", my_classes))
    application.add_handler(CommandHandler("add_student", add_student))
    application.add_handler(upload_consent_conv_handler)
    application.add_handler(CommandHandler("my_consents", my_consents))
    application.add_handler(submit_consent_conv_handler)
    application.add_handler(reports_conv_handler)

    # Добавляем задачу в JobQueue для проверки дедлайнов (например, каждые 60 минут)
    job_queue = application.job_queue
    job_queue.run_repeating(check_deadlines, interval=3600, first=10) # Первый запуск через 10 секунд, затем каждые 60 минут

    # Добавляем задачу в JobQueue для проверки приближающихся дедлайнов (например, один раз в день)
    # Первый запуск через 60 секунд, затем каждые 24 часа (86400 секунд)
    job_queue.run_repeating(check_upcoming_deadlines, interval=86400, first=60)

    # Запуск бота
    logger.info("Запуск бота...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()