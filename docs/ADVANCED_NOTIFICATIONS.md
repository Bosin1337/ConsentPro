# Расширенная система уведомлений

## Функционал

- Отправка напоминаний о приближающихся дедлайнах.

## План реализации

1.  **`utils/scheduler.py`**:
    - Написать асинхронную функцию `check_upcoming_deadlines(context)`.
2.  **`bot/main.py`**:
    - Интегрировать `check_upcoming_deadlines` в `job_queue`.