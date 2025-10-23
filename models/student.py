from db.connection import get_db_connection
from psycopg2.extras import RealDictCursor
from models.user import create_user
import logging

logger = logging.getLogger(__name__)

def add_student_and_parent(class_id: int, student_full_name: str, parent_full_name: str):
    """
    Добавляет ученика в класс и создает для родителя "заглушку" в таблице users (роль "Родитель").
    Затем связывает родителя и ученика в таблице parents.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # 1. Создаем "заглушку" для родителя в таблице users
            # Родитель пока не зарегистрирован в боте, но у него есть "заглушка" для связи с учеником.
            # Мы создаем пользователя с telegram_id = NULL или используем другой подход.
            # В данном случае, я создам пользователя с telegram_id = 0 (что означает, что он не зарегистрирован).
            # В реальном приложении telegram_id будет заполнен, когда родитель зарегистрируется.
            # Мы создаем пользователя с ролью "Родитель" (id=3).
            cursor.execute(
                "INSERT INTO users (telegram_id, role_id) VALUES (0, 3) RETURNING id;",
                ()
            )
            parent_user_id = cursor.fetchone()['id']

            # 2. Создаем запись об ученике
            cursor.execute(
                "INSERT INTO students (full_name, class_id) VALUES (%s, %s) RETURNING id;",
                (student_full_name, class_id)
            )
            student_id = cursor.fetchone()['id']

            # 3. Создаем связь между родителем (его "заглушкой" в users) и учеником в таблице parents
            cursor.execute(
                "INSERT INTO parents (user_id, student_id) VALUES (%s, %s);",
                (parent_user_id, student_id)
            )

            conn.commit()
            logger.info(f"Добавлен ученик '{student_full_name}' (id {student_id}) в класс {class_id}. Создана связь с родителем (user_id {parent_user_id}).")
            return student_id
    except Exception as e:
        logger.error(f"Ошибка при добавлении ученика '{student_full_name}' и родителя: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()