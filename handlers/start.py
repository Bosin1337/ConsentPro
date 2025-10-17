from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user_by_telegram_id, create_user
import logging

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /start"""
    user = update.effective_user
    telegram_id = user.id

    # Проверяем, есть ли пользователь в базе данных
    user_data = get_user_by_telegram_id(telegram_id)

    if user_data:
        # Пользователь уже существует
        role_name = user_data['role_name']
        logger.info(f"Пользователь {telegram_id} (роль: {role_name}) снова нажал /start.")
        await update.message.reply_html(
            rf"Привет, {user.mention_html()}! Вы авторизованы как {role_name}. Используйте /help для получения списка команд."
        )
    else:
        # Новый пользователь - создаем его с ролью "Родитель" (id=3)
        # В реальном приложении здесь может быть более сложная логика (например, ввод кода приглашения).
        # Пока что просто создаем с ролью "Родитель".
        create_user(telegram_id, role_id=3)  # 3 - id роли "Родитель"
        logger.info(f"Зарегистрирован новый пользователь {telegram_id} с ролью 'Родитель'.")
        await update.message.reply_html(
            rf"Привет, {user.mention_html()}! Вы успешно зарегистрировались как Родитель. Используйте /help для получения списка команд."
        )