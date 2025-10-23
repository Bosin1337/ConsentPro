from telegram import Update
from telegram.ext import ContextTypes
from models.class_ import get_classes_by_teacher, create_class
from models.student import add_student_and_parent
from utils.auth import require_role
import logging

logger = logging.getLogger(__name__)

@require_role(['Учитель'])
async def add_class(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создает новый класс."""
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Использование: /add_class <Название класса>")
        return

    class_name = " ".join(context.args)
    teacher_telegram_id = update.effective_user.id

    from models.user import get_user_by_telegram_id
    teacher_data = get_user_by_telegram_id(teacher_telegram_id)
    if not teacher_data:
        await update.message.reply_text("Ошибка: Не удалось получить данные учителя.")
        return

    teacher_id = teacher_data['id']
    new_class_id = create_class(class_name, teacher_id)

    if new_class_id:
        await update.message.reply_text(f"Класс '{class_name}' успешно создан с ID {new_class_id}.")
    else:
        await update.message.reply_text(f"Ошибка при создании класса '{class_name}'.")


@require_role(['Учитель'])
async def my_classes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список классов учителя."""
    teacher_telegram_id = update.effective_user.id

    from models.user import get_user_by_telegram_id
    teacher_data = get_user_by_telegram_id(teacher_telegram_id)
    if not teacher_data:
        await update.message.reply_text("Ошибка: Не удалось получить данные учителя.")
        return

    teacher_id = teacher_data['id']
    classes = get_classes_by_teacher(teacher_id)

    if not classes:
        await update.message.reply_text("У вас нет созданных классов.")
        return

    class_list_text = "\n".join([f"ID: {cls['id']}, Название: {cls['name']}" for cls in classes])
    await update.message.reply_text(f"Ваши классы:\n{class_list_text}")


@require_role(['Учитель'])
async def add_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавляет ученика и родителя."""
    if not context.args or len(context.args) < 3:
        await update.message.reply_text("Использование: /add_student <ID класса> <ФИО ученика> <ФИО родителя>")
        return

    try:
        class_id = int(context.args[0])
        student_full_name = " ".join(context.args[1:-1])  # Все аргументы, кроме первого и последнего
        parent_full_name = context.args[-1]  # Последний аргумент
    except ValueError:
        await update.message.reply_text("Неверный формат. Убедитесь, что ID класса - это число.")
        return

    student_id = add_student_and_parent(class_id, student_full_name, parent_full_name)

    if student_id:
        await update.message.reply_text(f"Ученик '{student_full_name}' и родитель '{parent_full_name}' успешно добавлены. ID ученика: {student_id}.")
    else:
        await update.message.reply_text(f"Ошибка при добавлении ученика '{student_full_name}'.")