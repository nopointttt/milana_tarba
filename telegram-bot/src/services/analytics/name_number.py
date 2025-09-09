"""src/services/analytics/name_number.py
Алгоритм расчёта Числа Имени по «Книге Знаний по Цифрологии» (система Миланы Тарба).

Источник (цитаты по файлу «Книга Знаний.txt»):
- «Для того, чтобы рассчитать Число имени, напишите своё имя на латинице» (стр. 3236-3237)
- «если у Вас имя пишется на кириллице, возьмите тот вариант, который написан в Вашем загранпаспорте» (стр. 3238-3239)

Таблица соответствий (стр. 3242-3248):
AIJQY = 1
BKR = 2  
CLSG = 3
DMT = 4
ENX = 5
FOUV = 6
GPW = 7
HQX = 8
IRY = 9

Пример расчёта (стр. 3281-3282):
Milana = 4+1+3+1+5+1=15=6
Число имени: 6 (6 – успех, к замужеству)
"""
from __future__ import annotations

from typing import Dict


# Таблица соответствий букв числам из «Книги Знаний»
LETTER_TO_NUMBER: Dict[str, int] = {
    # 1
    'A': 1, 'I': 1, 'J': 1, 'Q': 1, 'Y': 1,
    # 2  
    'B': 2, 'K': 2, 'R': 2,
    # 3
    'C': 3, 'L': 3, 'S': 3, 'G': 3,
    # 4
    'D': 4, 'M': 4, 'T': 4,
    # 5
    'E': 5, 'N': 5, 'X': 5,
    # 6
    'F': 6, 'O': 6, 'U': 6, 'V': 6,
    # 7
    'P': 7, 'W': 7,
    # 8
    'H': 8, 'Z': 8,
    # 9
}

# Обратная таблица для получения букв по числу
NUMBER_TO_LETTERS: Dict[int, str] = {
    1: "AIJQY",
    2: "BKR", 
    3: "CLSG",
    4: "DMT",
    5: "ENX",
    6: "FOUV",
    7: "GPW",
    8: "HZ",
    9: "IRY"
}


def _digit_sum(n: int) -> int:
    """Вернуть сумму цифр числа n."""
    n = abs(n)
    s = 0
    while n:
        s += n % 10
        n //= 10
    return s


def _reduce_to_single_digit(n: int) -> int:
    """Свернуть число до однозначного (1..9) повторной суммой цифр."""
    if n <= 0:
        raise ValueError("Ожидалось положительное число")
    while n > 9:
        n = _digit_sum(n)
    return n


def calc_name_number(name: str) -> int:
    """Рассчитать Число Имени по таблице из «Книги Знаний».
    
    Алгоритм:
    1. Берём имя на латинице
    2. Каждой букве ставим в соответствие число по таблице
    3. Суммируем все числа
    4. Сворачиваем до однозначного числа (1..9)
    
    :param name: Имя на латинице (например, "Milana")
    :return: Число Имени (1..9)
    :raises ValueError: если имя содержит недопустимые символы
    """
    if not name or not name.strip():
        raise ValueError("Имя не может быть пустым")
    
    name = name.strip().upper()
    total_sum = 0
    
    for letter in name:
        if letter in LETTER_TO_NUMBER:
            total_sum += LETTER_TO_NUMBER[letter]
        elif letter == ' ':
            # Пробелы игнорируем
            continue
        else:
            raise ValueError(f"Недопустимый символ в имени: '{letter}'. Используйте только латинские буквы.")
    
    if total_sum == 0:
        raise ValueError("Имя должно содержать хотя бы одну букву")
    
    return _reduce_to_single_digit(total_sum)


def get_name_interpretation(name_number: int) -> str:
    """Получить интерпретацию Числа Имени.
    
    :param name_number: Число Имени (1..9)
    :return: Краткая интерпретация
    """
    interpretations = {
        1: "Лидерство, независимость, оригинальность",
        2: "Дипломатия, сотрудничество, чувствительность", 
        3: "Творчество, самовыражение, оптимизм",
        4: "Практичность, стабильность, трудолюбие",
        5: "Свобода, приключения, перемены",
        6: "Гармония, ответственность, забота",
        7: "Духовность, анализ, интуиция",
        8: "Материальный успех, власть, организация",
        9: "Завершение, мудрость, служение"
    }
    
    return interpretations.get(name_number, "Неизвестное число")


def validate_latin_name(name: str) -> bool:
    """Проверить, что имя содержит только латинские буквы.
    
    :param name: Имя для проверки
    :return: True если имя валидно
    """
    if not name or not name.strip():
        return False
    
    name = name.strip().upper()
    for letter in name:
        if letter != ' ' and letter not in LETTER_TO_NUMBER:
            return False
    
    return True


def get_available_letters_for_number(number: int) -> str:
    """Получить буквы, соответствующие числу.
    
    :param number: Число 1-9
    :return: Строка с буквами для этого числа
    """
    return NUMBER_TO_LETTERS.get(number, "")
