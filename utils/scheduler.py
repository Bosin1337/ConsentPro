from telegram.ext import ContextTypes
from db.connection import get_db_connection
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

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