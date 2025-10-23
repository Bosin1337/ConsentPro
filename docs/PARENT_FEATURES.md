# Функционал Родителя

## Команды

1.  `/my_consents`: Показывает список согласий для ребенка.
2.  `/submit_consent <ID согласия>`: Позволяет загрузить подписанный документ.

## План реализации

1.  **`models/consent.py`**:
    - Написать функцию `get_consents_by_parent`.
    - Написать функцию `update_submission_status`.
2.  **`handlers/parent.py`**:
    - Реализовать функцию `my_consents`.
    - Реализовать `ConversationHandler` для `/submit_consent`.
    - Защитить функции декоратором `@require_role(['Родитель'])`.
3.  **`bot/main.py`**:
    - Интегрировать новые обработчики.