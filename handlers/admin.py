from telegram import Update
from telegram.ext import ContextTypes
from models.user import get_user_by_telegram_id, assign_role_to_user
from utils.auth import require_role
import logging

logger = logging.getLogger(__name__)

@require_role(['Администратор'])
async def add_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назначает пользователю роль 'Учитель'."""
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Использование: /add_teacher <telegram_id>")
        return

    try:
        telegram_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный формат telegram_id. Укажите числовое значение.")
        return

    user_data = get_user_by_telegram_id(telegram_id)

    if not user_data:
        await update.message.reply_text(f"Пользователь с telegram_id {telegram_id} не найден в базе данных.")
        return

    # Предположим, что id роли "Учитель" = 2
    assign_role_to_user(telegram_id, new_role_id=2)
    await update.message.reply_text(f"Пользователю с telegram_id {telegram_id} успешно назначена роль 'Учитель'.")


@require_role(['Администратор'])
async def remove_teacher(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отзывает у пользователя роль 'Учитель', возвращая ему роль 'Родитель'."""
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Использование: /remove_teacher <telegram_id>")
        return

    try:
        telegram_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный формат telegram_id. Укажите числовое значение.")
        return

    user_data = get_user_by_telegram_id(telegram_id)

    if not user_data:
        await update.message.reply_text(f"Пользователь с telegram_id {telegram_id} не найден в базе данных.")
        return

    current_role = user_data['role_name']

    if current_role != 'Учитель':
        await update.message.reply_text(f"Пользователь с telegram_id {telegram_id} не является 'Учителем'. Его текущая роль: {current_role}.")
        return

    # Предположим, что id роли "Родитель" = 3
    assign_role_to_user(telegram_id, new_role_id=3)
    await update.message.reply_text(f"У пользователя с telegram_id {telegram_id} отозвана роль 'Учитель'. Назначена роль 'Родитель'.")