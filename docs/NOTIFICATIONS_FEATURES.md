# Система уведомлений (базовая)

## Функционал

- Отправка уведомлений родителям о новом согласии.

## План реализации

1.  **`utils/notifications.py`**:
    - Написать асинхронную функцию `send_notification_to_parents(class_id, consent_name)`.
2.  **`handlers/consent.py`**:
    - Интегрировать вызов `send_notification_to_parents` после создания согласия.