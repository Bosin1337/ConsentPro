# Функционал Учителя (базовый)

## Команды

1.  `/add_class <Название класса>`: Создает новый класс.
2.  `/my_classes`: Показывает список классов.
3.  `/add_student <ID класса> <ФИО ученика> <ФИО родителя>`: Добавляет ученика и родителя.

## План реализации

1.  **`models/class.py` и `models/student.py`**:
    - `models/class.py`: Функции `create_class`, `get_classes_by_teacher`.
    - `models/student.py`: Функция `add_student_and_parent`.
2.  **`handlers/teacher.py`**:
    - Реализовать функции `add_class`, `my_classes`, `add_student`.
    - Защитить функции декоратором `@require_role(['Учитель'])`.
3.  **`bot/main.py`**:
    - Интегрировать новые обработчики.