from db.connection import get_db_connection
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_consent(name: str, file_path: str, deadline_str: str, class_id: int):
    """
    Создает новое согласие и автоматически создает записи в consent_submissions
    для всех учеников в указанном классе.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 1. Создаем запись о согласии
            cursor.execute(
                "INSERT INTO consents (name, file_path, deadline, class_id) VALUES (%s, %s, %s, %s) RETURNING id;",
                (name, file_path, deadline_str, class_id)
            )
            consent_id = cursor.fetchone()['id']

            # 2. Получаем всех учеников из класса
            cursor.execute(
                "SELECT id FROM students WHERE class_id = %s;",
                (class_id,)
            )
            students = cursor.fetchall()

            # 3. Создаем записи в consent_submissions для каждого ученика
            for student in students:
                student_id = student['id']
                cursor.execute(
                    "INSERT INTO consent_submissions (student_id, consent_id, status) VALUES (%s, %s, 'Не сдано');",
                    (student_id, consent_id)
                )

            conn.commit()
            logger.info(f"Создано новое согласие '{name}' (id {consent_id}) для класса {class_id}. Создано {len(students)} записей для учеников.")
            return consent_id
    except Exception as e:
        logger.error(f"Ошибка при создании согласия '{name}' для класса {class_id}: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_consents_by_class(class_id: int):
    """
    Получает список согласий, созданных для указанного класса.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id, name, file_path, deadline FROM consents WHERE class_id = %s ORDER BY created_at DESC;",
                (class_id,)
            )
            consents = cursor.fetchall()
            return consents
    except Exception as e:
        logger.error(f"Ошибка при получении согласий для класса {class_id}: {e}")
        return []
    finally:
        conn.close()


def get_consent_by_id(consent_id: int):
    """
    Получает информацию о конкретном согласии по его ID.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id, name, file_path, deadline, class_id FROM consents WHERE id = %s;",
                (consent_id,)
            )
            consent = cursor.fetchone()
            return consent
    except Exception as e:
        logger.error(f"Ошибка при получении согласия с id {consent_id}: {e}")
        return None
    finally:
        conn.close()