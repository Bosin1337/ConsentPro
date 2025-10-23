from db.connection import get_db_connection
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

def generate_status_report(consent_id: int) -> str:
    """
    Генерирует текстовый отчет по статусам сдачи согласия для указанного consent_id.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Получаем название согласия
            cursor.execute("SELECT name FROM consents WHERE id = %s;", (consent_id,))
            consent_data = cursor.fetchone()
            if not consent_data:
                return f"Ошибка: Согласие с ID {consent_id} не найдено."

            consent_name = consent_data['name']

            # Получаем статистику по статусам
            cursor.execute("""
                SELECT
                    status,
                    COUNT(*) as count
                FROM
                    consent_submissions
                WHERE
                    consent_id = %s
                GROUP BY
                    status;
            """, (consent_id,))
            status_counts = cursor.fetchall()

            # Формируем заголовок отчета
            report_lines = [f"📊 Отчет по согласию '{consent_name}' (ID: {consent_id})", ""]

            if not status_counts:
                report_lines.append("Нет данных о сдаче согласия.")
                return "\n".join(report_lines)

            # Добавляем статистику по статусам
            report_lines.append("📈 Статистика по статусам:")
            total_submissions = 0
            for sc in status_counts:
                report_lines.append(f"  - {sc['status']}: {sc['count']}")
                total_submissions += sc['count']

            report_lines.append(f"  - Всего: {total_submissions}")
            report_lines.append("")

            # Получаем список учеников по каждому статусу
            for sc in status_counts:
                status = sc['status']
                report_lines.append(f"👥 Ученики со статусом '{status}':")
                cursor.execute("""
                    SELECT
                        s.full_name
                    FROM
                        consent_submissions cs
                    JOIN
                        students s ON cs.student_id = s.id
                    WHERE
                        cs.consent_id = %s AND cs.status = %s
                    ORDER BY
                        s.full_name;
                """, (consent_id, status))
                students = cursor.fetchall()
                for student in students:
                    report_lines.append(f"  - {student['full_name']}")

            return "\n".join(report_lines)

    except Exception as e:
        logger.error(f"Ошибка при генерации отчета по статусам для согласия {consent_id}: {e}")
        return f"Ошибка при генерации отчета: {e}"
    finally:
        conn.close()


def generate_class_statistics_report() -> str:
    """
    Генерирует статистический отчет по всем классам.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Получаем список всех классов
            cursor.execute("SELECT id, name FROM classes ORDER BY name;")
            classes = cursor.fetchall()

            if not classes:
                return "Нет данных о классах."

            # Формируем заголовок отчета
            report_lines = ["📊 Сводная статистика по классам", ""]

            for class_info in classes:
                class_id = class_info['id']
                class_name = class_info['name']
                report_lines.append(f"🏫 Класс: {class_name}")

                # Получаем все согласия для этого класса
                cursor.execute("""
                    SELECT
                        id,
                        name
                    FROM
                        consents
                    WHERE
                        class_id = %s
                    ORDER BY
                        created_at DESC;
                """, (class_id,))
                consents = cursor.fetchall()

                if not consents:
                    report_lines.append("  Нет согласий для этого класса.")
                    report_lines.append("")
                    continue

                # Для каждого согласия получаем статистику
                for consent in consents:
                    consent_id = consent['id']
                    consent_name = consent['name']
                    report_lines.append(f"  📄 Согласие: {consent_name} (ID: {consent_id})")

                    cursor.execute("""
                        SELECT
                            status,
                            COUNT(*) as count
                        FROM
                            consent_submissions
                        WHERE
                            consent_id = %s
                        GROUP BY
                            status;
                    """, (consent_id,))
                    status_stats = cursor.fetchall()

                    total_in_class = 0
                    stats_dict = {}
                    for stat in status_stats:
                        stats_dict[stat['status']] = stat['count']
                        total_in_class += stat['count']

                    # Рассчитываем проценты
                    if total_in_class > 0:
                        submitted_count = stats_dict.get('Сдано', 0)
                        refused_count = stats_dict.get('Отказался', 0)
                        expired_count = stats_dict.get('Просрочено', 0)
                        not_submitted_count = stats_dict.get('Не сдано', 0)

                        submitted_percent = (submitted_count / total_in_class) * 100
                        refused_percent = (refused_count / total_in_class) * 100
                        expired_percent = (expired_count / total_in_class) * 100
                        not_submitted_percent = (not_submitted_count / total_in_class) * 100

                        report_lines.append(f"    ✅ Сдано: {submitted_count} ({submitted_percent:.1f}%)")
                        report_lines.append(f"    ❌ Отказано: {refused_count} ({refused_percent:.1f}%)")
                        report_lines.append(f"    ⏰ Просрочено: {expired_count} ({expired_percent:.1f}%)")
                        report_lines.append(f"    🕒 Не сдано: {not_submitted_count} ({not_submitted_percent:.1f}%)")
                    else:
                        report_lines.append("    Нет данных о сдаче.")

                report_lines.append("") # Пустая строка между классами

            return "\n".join(report_lines)

    except Exception as e:
        logger.error(f"Ошибка при генерации сводного отчета по классам: {e}")
        return f"Ошибка при генерации сводного отчета: {e}"
    finally:
        conn.close()