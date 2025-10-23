# Интеграция ИИ для анализа документов

## Функционал

- Автоматическое определение статуса согласия ("Сдано", "Отказался") на основе анализа текста загруженного документа.

## План реализации

1.  **`requirements.txt`**:
    - Добавить `PyMuPDF` и `python-docx`.
2.  **`utils/document_analyzer.py`**:
    - Написать функцию `analyze_document(file_path)`.
3.  **`handlers/parent.py`**:
    - Интегрировать вызов `analyze_document` в `handle_file_submission`.