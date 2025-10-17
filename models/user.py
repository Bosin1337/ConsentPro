from db.connection import get_db_connection
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def get_user_by_telegram_id(telegram_id: int):
    """Получает информацию о пользователе по его telegram_id."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT u.id, u.telegram_id, r.name AS role_name FROM users u JOIN roles r ON u.role_id = r.id WHERE u.telegram_id = %s;",
                (telegram_id,)
            )
            user_data = cursor.fetchone()
            return user_data
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя по telegram_id {telegram_id}: {e}")
        return None
    finally:
        conn.close()

def create_user(telegram_id: int, role_id: int = 3): # По умолчанию роль "Родитель" (id=3)
    """Создает нового пользователя с указанным telegram_id и role_id. Роль по умолчанию - 'Родитель'."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (telegram_id, role_id) VALUES (%s, %s);",
                (telegram_id, role_id)
            )
            conn.commit()
            logger.info(f"Создан новый пользователь с telegram_id {telegram_id} и role_id {role_id}.")
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя с telegram_id {telegram_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

def assign_role_to_user(telegram_id: int, new_role_id: int):
    """Назначает пользователю новую роль по его telegram_id."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET role_id = %s WHERE telegram_id = %s;",
                (new_role_id, telegram_id)
            )
            conn.commit()
            logger.info(f"Пользователю с telegram_id {telegram_id} назначена роль с id {new_role_id}.")
    except Exception as e:
        logger.error(f"Ошибка при назначении роли пользователю с telegram_id {telegram_id}: {e}")
        conn.rollback()
    finally:
        conn.close()