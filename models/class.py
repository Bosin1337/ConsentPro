from db.connection import get_db_connection
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def create_class(name: str, teacher_id: int):
    """Создает новый класс, привязанный к учителю."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "INSERT INTO classes (name, teacher_id) VALUES (%s, %s) RETURNING id;",
                (name, teacher_id)
            )
            new_class_id = cursor.fetchone()['id']
            conn.commit()
            logger.info(f"Создан новый класс '{name}' с id {new_class_id} для учителя с id {teacher_id}.")
            return new_class_id
    except Exception as e:
        logger.error(f"Ошибка при создании класса '{name}' для учителя {teacher_id}: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_classes_by_teacher(teacher_id: int):
    """Получает список классов, созданных учителем."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id, name FROM classes WHERE teacher_id = %s ORDER BY name;",
                (teacher_id,)
            )
            classes = cursor.fetchall()
            return classes
    except Exception as e:
        logger.error(f"Ошибка при получении классов для учителя {teacher_id}: {e}")
        return []
    finally:
        conn.close()