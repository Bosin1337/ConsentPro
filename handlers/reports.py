from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from utils.auth import require_role
from utils.reports import generate_status_report, generate_class_statistics_report
import logging

logger = logging.getLogger(__name__)

# Константы для состояний разговора
REPORT_TYPE, CONSENT_ID = range(2)

@require_role(['Учитель', 'Администратор'])
async def reports_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало разговора для выбора типа отчета."""
    user_role = context.user_data.get('role_name')

    keyboard = [
        [InlineKeyboardButton("Список учеников по статусам", callback_data="status_report")],
    ]

    if user_role == 'Администратор':
        keyboard.append([InlineKeyboardButton("Статистика сдачи по классам", callback_data="class_stats_report")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите тип отчета:", reply_markup=reply_markup)
    return REPORT_TYPE

async def handle_report_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение выбранного типа отчета."""
    query = update.callback_query
    await query.answer()

    selected_report_type = query.data
    context.user_data['selected_report_type'] = selected_report_type

    if selected_report_type == "status_report":
        await query.edit_message_text("Введите ID согласия для генерации отчета по статусам.")
        return CONSENT_ID
    elif selected_report_type == "class_stats_report":
        # Генерируем и отправляем сводный отчет
        report_text = generate_class_statistics_report()
        # Отправляем отчет по частям, если он слишком длинный
        if len(report_text) > 4096:
            for i in range(0, len(report_text), 4096):
                await update.effective_message.reply_text(report_text[i:i + 4096])
        else:
            await query.edit_message_text(report_text)
        return ConversationHandler.END

async def handle_consent_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение ID согласия и генерация отчета."""
    user_data = context.user_data
    consent_id_text = update.message.text

    try:
        consent_id = int(consent_id_text)
    except ValueError:
        await update.message.reply_text("Неверный формат ID согласия. Пожалуйста, введите числовое значение.")
        return CONSENT_ID

    # Генерируем отчет
    report_text = generate_status_report(consent_id)

    # Отправляем отчет по частям, если он слишком длинный
    if len(report_text) > 4096:
        for i in range(0, len(report_text), 4096):
            await update.message.reply_text(report_text[i:i + 4096])
    else:
        await update.message.reply_text(report_text)

    # Очищаем user_data
    user_data.clear()

    return ConversationHandler.END

async def cancel_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена разговора."""
    await update.message.reply_text("Генерация отчета отменена.")
    context.user_data.clear()
    return ConversationHandler.END

# Определяем ConversationHandler
reports_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('reports', reports_start)],
    states={
        REPORT_TYPE: [CallbackQueryHandler(handle_report_type_selection)],
        CONSENT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_consent_id_input)],
    },
    fallbacks=[CommandHandler('cancel', cancel_reports)]
)