import fitz  # PyMuPDF
from docx import Document
import logging
import os

logger = logging.getLogger(__name__)

# Слова-маркеры для определения статуса "Отказался"
REFUSAL_KEYWORDS = [
    "отказываюсь",
    "не согласен",
    "против",
    "отказ",
    "не даю согласие",
    "не разрешаю"
]

def analyze_document(file_path: str) -> str:
    """
    Анализирует документ и возвращает статус: "Сдано" или "Отказался".
    """
    if not os.path.exists(file_path):
        logger.error(f"Файл {file_path} не найден.")
        return "Сдано"  # По умолчанию, если файл не найден

    text = ""
    file_extension = os.path.splitext(file_path)[1].lower()

    try:
        if file_extension == '.pdf':
            # Извлечение текста из PDF
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        elif file_extension == '.docx':
            # Извлечение текста из DOCX
            doc = Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        else:
            logger.warning(f"Неподдерживаемый формат файла: {file_extension}")
            return "Сдано" # По умолчанию для неподдерживаемых форматов

        # Приводим текст к нижнему регистру для поиска
        text_lower = text.lower()

        # Проверяем наличие слов-маркеров отказа
        for keyword in REFUSAL_KEYWORDS:
            if keyword in text_lower:
                logger.info(f"Найдено слово-маркер отказа '{keyword}' в документе {file_path}.")
                return "Отказался"

        # Если маркеры не найдены, считаем, что согласие дано
        logger.info(f"Слова-маркеры отказа не найдены в документе {file_path}. Статус: Сдано.")
        return "Сдано"

    except Exception as e:
        logger.error(f"Ошибка при анализе документа {file_path}: {e}")
        # В случае ошибки анализа, по умолчанию считаем "Сдано"
        return "Сдано"