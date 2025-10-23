from telegram.ext import Application
import logging
from db.connection import get_db_connection
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

async def send_notification_to_parents(application: Application, class_id: int, consent_name: str):
    """
    Отправляет уведомление родителям учеников из указанного класса о новом согласии.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Получаем telegram_id всех родителей, чьи дети находятся в данном классе
            cursor.execute("""
                SELECT DISTINCT u.telegram_id
                FROM users u
                JOIN parents p ON u.id = p.user_id
                JOIN students s ON p.student_id = s.id
                WHERE s.class_id = %s AND u.telegram_id != 0; -- telegram_id = 0 означает, что пользователь не зарегистрирован
            """, (class_id,))
            parent_telegram_ids = cursor.fetchall()

            for parent_data in parent_telegram_ids:
                parent_telegram_id = parent_data['telegram_id']
                try:
                    await application.bot.send_message(
                        chat_id=parent_telegram_id,
                        text=f"Доступно новое согласие для вашего ребенка: {consent_name}. Пожалуйста, проверьте команду /my_consents."
                    )
                    logger.info(f"Уведомление отправлено родителю с telegram_id {parent_telegram_id} о согласии '{consent_name}'.")
                except Exception as e:
                    # Возможна ошибка, если родитель заблокировал бота
                    logger.error(f"Не удалось отправить уведомление родителю с telegram_id {parent_telegram_id}: {e}")

    except Exception as e:
        logger.error(f"Ошибка при получении списка родителей для класса {class_id} для уведомления: {e}")
    finally:
        conn.close()