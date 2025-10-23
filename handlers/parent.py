from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from models.consent import get_consents_by_parent, update_submission_status
from utils.auth import require_role
from utils.document_analyzer import analyze_document
import logging
import os

logger = logging.getLogger(__name__)

# Константы для состояний разговора
CONSENT_ID, FILE = range(2)

@require_role(['Родитель'])
async def my_consents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список согласий для ребенка."""
    parent_telegram_id = update.effective_user.id

    from models.user import get_user_by_telegram_id
    parent_data = get_user_by_telegram_id(parent_telegram_id)
    if not parent_data:
        await update.message.reply_text("Ошибка: Не удалось получить данные родителя.")
        return

    parent_user_id = parent_data['id']
    consents = get_consents_by_parent(parent_user_id)

    if not consents:
        await update.message.reply_text("Нет согласий для отображения.")
        return

    consent_list_text = "\n".join([
        f"ID: {c['consent_id']}, Название: {c['consent_name']}, Статус: {c['submission_status']}, Дедлайн: {c['deadline']}"
        for c in consents
    ])
    await update.message.reply_text(f"Согласия для вашего ребенка:\n{consent_list_text}")


@require_role(['Родитель'])
async def submit_consent_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало разговора для загрузки согласия."""
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Использование: /submit_consent <ID согласия>")
        return

    try:
        consent_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Неверный формат ID согласия. Укажите числовое значение.")
        return

    # Проверим, существует ли такое согласие для этого родителя
    parent_telegram_id = update.effective_user.id
    from models.user import get_user_by_telegram_id
    parent_data = get_user_by_telegram_id(parent_telegram_id)
    if not parent_data:
        await update.message.reply_text("Ошибка: Не удалось получить данные родителя.")
        return

    parent_user_id = parent_data['id']
    consents = get_consents_by_parent(parent_user_id)

    consent_exists = False
    consent_submission_id = None
    for c in consents:
        if c['consent_id'] == consent_id:
            consent_exists = True
            consent_submission_id = c['consent_submission_id']
            break

    if not consent_exists:
        await update.message.reply_text(f"Согласие с ID {consent_id} не найдено или не относится к вашему ребенку.")
        return

    # Сохраняем ID в user_data
    context.user_data['consent_submission_id'] = consent_submission_id

    await update.message.reply_text(f"Отправьте подписанный PDF или DOCX файл для согласия с ID {consent_id}.")
    return FILE

async def handle_file_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение файла согласия, сохранение на диск и анализ."""
    user_data = context.user_data
    file = update.message.document

    if not file:
        await update.message.reply_text("Пожалуйста, отправьте файл.")
        return FILE

    # Проверка типа файла
    file_extension = os.path.splitext(file.file_name)[1].lower()
    if file_extension not in ['.pdf', '.docx']:
        await update.message.reply_text("Неподдерживаемый формат файла. Пожалуйста, отправьте PDF или DOCX файл.")
        return FILE

    # Скачивание файла
    try:
        file_id = file.file_id
        new_file = await context.bot.get_file(file_id)
        # Сохраняем файл в папку uploads (ее нужно создать заранее)
        file_path = f"uploads/{file.file_name}"
        await new_file.download_to_drive(custom_path=file_path)

        # Анализируем документ с помощью ИИ
        ai_determined_status = analyze_document(file_path)
        logger.info(f"ИИ определил статус согласия как: {ai_determined_status}")

        # Обновляем статус в базе данных с учетом анализа ИИ
        submission_id = user_data.get('consent_submission_id')
        if submission_id:
            update_submission_status(submission_id, ai_determined_status, file_path)
            await update.message.reply_text(f"Файл '{file.file_name}' успешно загружен. Статус согласия определен как '{ai_determined_status}'.")
        else:
            await update.message.reply_text("Произошла ошибка при обновлении статуса.")

        # Очищаем user_data
        user_data.clear()

        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Ошибка при скачивании или анализе файла: {e}")
        await update.message.reply_text("Произошла ошибка при загрузке или анализе файла. Попробуйте еще раз.")
        return FILE

async def cancel_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена разговора."""
    await update.message.reply_text("Загрузка согласия отменена.")
    context.user_data.clear()
    return ConversationHandler.END

# Определяем ConversationHandler
submit_consent_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('submit_consent', submit_consent_start)],
    states={
        FILE: [MessageHandler(filters.Document.ALL, handle_file_submission)],
    },
    fallbacks=[CommandHandler('cancel', cancel_submission)]
)