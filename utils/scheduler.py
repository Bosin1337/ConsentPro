from telegram.ext import ContextTypes
from db.connection import get_db_connection
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

async def check_deadlines(context: ContextTypes.DEFAULT_TYPE):
    """
    Периодически проверяет дедлайны согласий и обновляет статусы.
    """
    logger.info("Начало проверки дедлайнов согласий...")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Получаем все согласия, у которых дедлайн прошел, но статус еще не "Просрочено"
            # Также получаем информацию о классе и учителе
            cursor.execute("""
                SELECT
                    c.id AS consent_id,
                    c.name AS consent_name,
                    c.deadline,
                    cl.teacher_id,
                    t.telegram_id AS teacher_telegram_id
                FROM
                    consents c
                JOIN
                    classes cl ON c.class_id = cl.id
                JOIN
                    users t ON cl.teacher_id = t.id
                WHERE
                    c.deadline < NOW() AT TIME ZONE 'UTC'
                    AND c.id IN (
                        SELECT DISTINCT consent_id
                        FROM consent_submissions
                        WHERE status != 'Просрочено'
                    );
            """)
            expired_consents = cursor.fetchall()

            if not expired_consents:
                logger.info("Нет согласий с просроченными дедлайнами.")
                return

            logger.info(f"Найдено {len(expired_consents)} согласий с просроченными дедлайнами.")

            for consent_data in expired_consents:
                consent_id = consent_data['consent_id']
                consent_name = consent_data['consent_name']
                teacher_telegram_id = consent_data['teacher_telegram_id']

                # Обновляем статус всех незавершенных сдач на "Просрочено"
                cursor.execute("""
                    UPDATE consent_submissions
                    SET status = 'Просрочено'
                    WHERE consent_id = %s AND status NOT IN ('Сдано', 'Отказался');
                """, (consent_id,))
                updated_rows = cursor.rowcount
                logger.info(f"Обновлено {updated_rows} записей для согласия '{consent_name}' (ID: {consent_id}) на статус 'Просрочено'.")

                # Формируем и отправляем сводку учителю
                if teacher_telegram_id and updated_rows > 0:
                    try:
                        # Получаем список учеников, которые не сдали согласие
                        cursor.execute("""
                            SELECT
                                s.full_name
                            FROM
                                consent_submissions cs
                            JOIN
                                students s ON cs.student_id = s.id
                            WHERE
                                cs.consent_id = %s AND cs.status = 'Просрочено';
                        """, (consent_id,))
                        students_with_expired = cursor.fetchall()
                        student_names = [s['full_name'] for s in students_with_expired]

                        summary_text = (
                            f"⚠️ Дедлайн по согласию '{consent_name}' (ID: {consent_id}) истек.\n"
                            f"Следующие ученики не сдали согласие вовремя:\n"
                            f"{chr(10).join(student_names)}"
                        )

                        await context.bot.send_message(chat_id=teacher_telegram_id, text=summary_text)
                        logger.info(f"Сводка отправлена учителю с telegram_id {teacher_telegram_id}.")
                    except Exception as e:
                        logger.error(f"Не удалось отправить сводку учителю с telegram_id {teacher_telegram_id}: {e}")

            conn.commit()

    except Exception as e:
        logger.error(f"Ошибка при проверке дедлайнов согласий: {e}")
        conn.rollback()
    finally:
        conn.close()
        logger.info("Проверка дедлайнов согласий завершена.")


async def check_upcoming_deadlines(context: ContextTypes.DEFAULT_TYPE):
    """
    Периодически проверяет приближающиеся дедлайны и отправляет напоминания.
    """
    logger.info("Начало проверки приближающихся дедлайнов согласий...")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Определяем дату, за 3 дня до которой нужно искать дедлайны
            # Например, если сегодня 2023-10-20, то ищем дедлайны 2023-10-23
            target_date = datetime.utcnow().date() + timedelta(days=3)
            logger.info(f"Проверяем дедлайны, приходящиеся на {target_date}.")

            # Получаем все согласия, у которых дедлайн приходится на target_date
            # Также получаем информацию о классе, учителе и родителях учеников
            cursor.execute("""
                SELECT
                    c.id AS consent_id,
                    c.name AS consent_name,
                    c.deadline,
                    cl.id AS class_id,
                    cl.name AS class_name,
                    cl.teacher_id,
                    t.telegram_id AS teacher_telegram_id
                FROM
                    consents c
                JOIN
                    classes cl ON c.class_id = cl.id
                JOIN
                    users t ON cl.teacher_id = t.id
                WHERE
                    DATE(c.deadline AT TIME ZONE 'UTC') = %s;
            """, (target_date,))
            upcoming_consents = cursor.fetchall()

            if not upcoming_consents:
                logger.info("Нет согласий с дедлайнами на указанную дату.")
                return

            logger.info(f"Найдено {len(upcoming_consents)} согласий с дедлайнами на {target_date}.")

            for consent_data in upcoming_consents:
                consent_id = consent_data['consent_id']
                consent_name = consent_data['consent_name']
                class_name = consent_data['class_name']
                teacher_telegram_id = consent_data['teacher_telegram_id']

                # Получаем список учеников, которые еще не сдали согласие (статус "Не сдано")
                cursor.execute("""
                    SELECT
                        s.id AS student_id,
                        s.full_name AS student_name,
                        p.user_id AS parent_user_id,
                        pu.telegram_id AS parent_telegram_id
                    FROM
                        consent_submissions cs
                    JOIN
                        students s ON cs.student_id = s.id
                    LEFT JOIN
                        parents p ON s.id = p.student_id
                    LEFT JOIN
                        users pu ON p.user_id = pu.id
                    WHERE
                        cs.consent_id = %s AND cs.status = 'Не сдано';
                """, (consent_id,))
                students_not_submitted = cursor.fetchall()

                if not students_not_submitted:
                    logger.info(f"Все ученики сдали согласие '{consent_name}' (ID: {consent_id}) или отказались от него.")
                    continue

                logger.info(f"Найдено {len(students_not_submitted)} учеников, которые еще не сдали согласие '{consent_name}'.")

                # Отправляем напоминания родителям
                reminder_text_to_parents = (
                    f"📅 Напоминание!\n"
                    f"Согласие '{consent_name}' для класса {class_name} должно быть сдано до {target_date.strftime('%d.%m.%Y')}.\n"
                    f"Пожалуйста, не забудьте сдать согласие вовремя."
                )

                for student_data in students_not_submitted:
                    parent_telegram_id = student_data['parent_telegram_id']
                    student_name = student_data['student_name']
                    if parent_telegram_id:
                        try:
                            await context.bot.send_message(chat_id=parent_telegram_id, text=reminder_text_to_parents)
                            logger.info(f"Напоминание отправлено родителю ученика {student_name} (telegram_id {parent_telegram_id}).")
                        except Exception as e:
                            logger.error(f"Не удалось отправить напоминание родителю ученика {student_name} (telegram_id {parent_telegram_id}): {e}")
                    else:
                        logger.warning(f"Родитель ученика {student_name} не зарегистрирован в боте (нет telegram_id).")

                # Отправляем сводку учителю
                if teacher_telegram_id:
                    try:
                        student_names_list = [s['student_name'] for s in students_not_submitted]
                        summary_text_to_teacher = (
                            f"📅 Сводка по приближающимся дедлайнам!\n"
                            f"Согласие '{consent_name}' для класса {class_name} должно быть сдано до {target_date.strftime('%d.%m.%Y')}.\n"
                            f"Следующие ученики еще не сдали согласие:\n"
                            f"{chr(10).join(student_names_list)}"
                        )
                        await context.bot.send_message(chat_id=teacher_telegram_id, text=summary_text_to_teacher)
                        logger.info(f"Сводка отправлена учителю с telegram_id {teacher_telegram_id}.")
                    except Exception as e:
                        logger.error(f"Не удалось отправить сводку учителю с telegram_id {teacher_telegram_id}: {e}")

    except Exception as e:
        logger.error(f"Ошибка при проверке приближающихся дедлайнов согласий: {e}")
        # conn.rollback() не нужен, так как мы только читаем данные
    finally:
        conn.close()
        logger.info("Проверка приближающихся дедлайнов согласий завершена.")