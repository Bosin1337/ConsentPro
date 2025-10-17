from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user_by_telegram_id
import logging

logger = logging.getLogger(__name__)

def require_role(allowed_roles: list):
    """
    Декоратор для проверки роли пользователя перед выполнением обработчика команды.

    Args:
        allowed_roles (list): Список строк с названиями разрешенных ролей (например, ['Учитель', 'Администратор']).
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_telegram_id = update.effective_user.id

            # Получаем информацию о пользователе из базы данных
            user_data = get_user_by_telegram_id(user_telegram_id)

            if not user_data:
                logger.warning(f"Пользователь с telegram_id {user_telegram_id} не найден в базе данных.")
                await update.message.reply_text("Вы не авторизованы. Пожалуйста, зарегистрируйтесь через команду /start.")
                return

            user_role = user_data['role_name']

            if user_role not in allowed_roles:
                logger.info(f"Пользователь с telegram_id {user_telegram_id} (роль: {user_role}) попытался выполнить команду, требующую роли: {allowed_roles}")
                await update.message.reply_text(f"У вас недостаточно прав для выполнения этой команды. Необходима роль: {', '.join(allowed_roles)}.")
                return

            # Если проверка пройдена, вызываем оригинальную функцию
            return await func(update, context)

        return wrapper
    return decorator