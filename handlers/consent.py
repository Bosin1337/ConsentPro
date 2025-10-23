from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from models.consent import create_consent
from models.class_ import get_classes_by_teacher
from utils.auth import require_role
from utils.notifications import send_notification_to_parents
import logging
import os

logger = logging.getLogger(__name__)

# Константы для состояний разговора
NAME, FILE, DEADLINE, CLASS = range(4)

@require_role(['Учитель'])
async def upload_consent_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало разговора для загрузки согласия."""
    await update.message.reply_text("Пожалуйста, введите название согласия.")
    return NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение названия согласия."""
    context.user_data['consent_name'] = update.message.text
    await update.message.reply_text(f"Название: {update.message.text}\nТеперь отправьте PDF или DOCX файл согласия.")
    return FILE

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение файла согласия и сохранение на диск."""
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

        user_data['file_path'] = file_path
        await update.message.reply_text(f"Файл '{file.file_name}' получен.\nТеперь введите дедлайн в формате ДД.ММ.ГГГГ (например, 25.12.2024).")
        return DEADLINE
    except Exception as e:
        logger.error(f"Ошибка при скачивании файла: {e}")
        await update.message.reply_text("Произошла ошибка при загрузке файла. Попробуйте еще раз.")
        return FILE

async def handle_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение дедлайна и запрос класса."""
    user_data = context.user_data
    deadline_text = update.message.text

    # Проверка формата дедлайна (упрощенная)
    try:
        # Попробуем распарсить дату
        from datetime import datetime
        deadline_dt = datetime.strptime(deadline_text, "%d.%m.%Y")
        user_data['deadline'] = deadline_dt.strftime("%Y-%m-%d %H:%M:%S") # Сохраняем в формате, подходящем для PostgreSQL
    except ValueError:
        await update.message.reply_text("Неверный формат даты. Пожалуйста, введите дедлайн в формате ДД.ММ.ГГГГ (например, 25.12.2024).")
        return DEADLINE

    await update.message.reply_text(f"Дедлайн: {deadline_text}\nТеперь выберите класс, для которого создается согласие.")

    # Получаем список классов учителя
    teacher_telegram_id = update.effective_user.id
    from models.user import get_user_by_telegram_id
    teacher_data = get_user_by_telegram_id(teacher_telegram_id)
    if not teacher_data:
        await update.message.reply_text("Ошибка: Не удалось получить данные учителя.")
        return ConversationHandler.END

    teacher_id = teacher_data['id']
    classes = get_classes_by_teacher(teacher_id)

    if not classes:
        await update.message.reply_text("У вас нет созданных классов.")
        return ConversationHandler.END

    # Создаем кнопки для выбора класса
    keyboard = []
    for class_info in classes:
        keyboard.append([InlineKeyboardButton(class_info['name'], callback_data=str(class_info['id']))])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите класс:", reply_markup=reply_markup)
    return CLASS

async def handle_class_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение выбранного класса и сохранение согласия."""
    query = update.callback_query
    await query.answer()

    user_data = context.user_data
    selected_class_id = int(query.data)

    # Сохраняем согласие в базу данных
    consent_id = create_consent(
        name=user_data.get('consent_name'),
        file_path=user_data.get('file_path'),
        deadline_str=user_data.get('deadline'),
        class_id=selected_class_id
    )

    if consent_id:
        await query.edit_message_text(f"Согласие '{user_data.get('consent_name')}' успешно создано для класса с ID {selected_class_id}!")
    else:
        await query.edit_message_text("Произошла ошибка при создании согласия. Попробуйте еще раз.")

    # Очищаем user_data
    user_data.clear()

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена разговора."""
    await update.message.reply_text("Создание согласия отменено.")
    context.user_data.clear()
    return ConversationHandler.END

# Определяем ConversationHandler
upload_consent_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('upload_consent', upload_consent_start)],
    states={
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
        FILE: [MessageHandler(filters.Document.ALL, handle_file)],
        DEADLINE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deadline)],
        CLASS: [CallbackQueryHandler(handle_class_selection)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)