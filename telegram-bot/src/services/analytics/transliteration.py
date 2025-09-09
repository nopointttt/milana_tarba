"""src/services/analytics/transliteration.py
Транслитерация кириллицы в латиницу по ГОСТ 7.79-2000.

Используется для преобразования имён с кириллицы на латиницу
перед расчётом Числа Имени согласно «Книге Знаний».
"""
from __future__ import annotations

from typing import Dict


# Таблица транслитерации по ГОСТ 7.79-2000
CYRILLIC_TO_LATIN: Dict[str, str] = {
    # Заглавные буквы
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'E',
    'Ж': 'ZH', 'З': 'Z', 'И': 'I', 'Й': 'J', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'KH', 'Ц': 'TS', 'Ч': 'CH', 'Ш': 'SH', 'Щ': 'SHCH',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'YU', 'Я': 'YA',
    
    # Строчные буквы
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'j', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    
    # Пробелы и дефисы
    ' ': ' ', '-': '-', "'": "'"
}


def transliterate_cyrillic_to_latin(text: str) -> str:
    """Транслитерировать текст с кириллицы на латиницу по ГОСТ 7.79-2000.
    
    :param text: Текст на кириллице
    :return: Текст на латинице в верхнем регистре
    """
    if not text:
        return ""
    
    result = []
    for char in text:
        if char in CYRILLIC_TO_LATIN:
            result.append(CYRILLIC_TO_LATIN[char])
        else:
            # Если символ не найден в таблице, оставляем как есть
            result.append(char)
    
    return ''.join(result).upper()


def is_cyrillic_text(text: str) -> bool:
    """Проверить, содержит ли текст кириллические символы.
    
    :param text: Текст для проверки
    :return: True если содержит кириллицу
    """
    if not text:
        return False
    
    for char in text:
        if '\u0400' <= char <= '\u04FF':  # Диапазон кириллических символов
            return True
    
    return False


def is_latin_text(text: str) -> bool:
    """Проверить, содержит ли текст только латинские символы.
    
    :param text: Текст для проверки
    :return: True если содержит только латиницу
    """
    if not text:
        return False
    
    for char in text:
        if char == ' ' or char == '-' or char == "'":
            continue
        if not ('A' <= char <= 'Z' or 'a' <= char <= 'z'):
            return False
    
    return True


def normalize_name_for_calculation(name: str) -> str:
    """Нормализовать имя для расчёта Числа Имени.
    
    Если имя на кириллице - транслитерирует в латиницу.
    Если уже на латинице - возвращает как есть.
    
    :param name: Имя (кириллица или латиница)
    :return: Имя на латинице, готовое для расчёта
    :raises ValueError: если имя содержит недопустимые символы
    """
    if not name or not name.strip():
        raise ValueError("Имя не может быть пустым")
    
    name = name.strip()
    
    # Проверяем на цифры и спецсимволы
    for char in name:
        if char.isdigit() or char in "!@#$%^&*()_+={}[]|\\:;\"'<>?,./":
            raise ValueError("Имя должно содержать только кириллические или латинские буквы")
    
    if is_cyrillic_text(name):
        # Транслитерируем с кириллицы
        latin_name = transliterate_cyrillic_to_latin(name)
        return latin_name.upper()
    elif is_latin_text(name):
        # Уже на латинице
        return name.upper()
    else:
        raise ValueError("Имя должно содержать только кириллические или латинские буквы")


def validate_name(name: str) -> bool:
    """Проверить, что имя содержит только латинские буквы (одно слово).
    
    :param name: Имя для проверки
    :return: True если имя валидно (только латиница, одно слово)
    """
    if not name or not name.strip():
        return False
    
    name = name.strip()
    
    # Проверяем, что это одно слово (нет пробелов)
    if ' ' in name:
        return False
    
    # Проверяем, что все символы - латинские буквы
    for char in name:
        if not (char.isalpha() and ord(char) < 128):
            return False
    
    return True


def get_transliteration_examples() -> Dict[str, str]:
    """Получить примеры транслитерации для демонстрации.
    
    :return: Словарь с примерами (кириллица -> латиница)
    """
    return {
        "Иван": "IVAN",
        "Анна": "ANNA",
        "Мария": "MARIYA",
        "Александр": "ALEKSANDR",
        "Екатерина": "EKATERINA",
        "Дмитрий": "DMITRIY",
        "Ольга": "OL'GA",
        "Сергей": "SERGEY",
        "Татьяна": "TAT'YANA",
        "Михаил": "MIKHAIL"
    }
