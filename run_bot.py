#!/usr/bin/env python3
"""
Исполняемый скрипт для запуска бота.
"""

import sys
import os

# Добавляем корневую папку проекта в PATH, чтобы можно было импортировать из bot.main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.main import main

if __name__ == '__main__':
    main()