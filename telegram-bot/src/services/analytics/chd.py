"""src/services/analytics/chd.py
Алгоритм расчёта Числа Действия (ЧД) по «Книге Знаний по Цифрологии» (система Миланы Тарба).

Источник (цитаты по файлу «Книга Знаний.txt»):
- «Число действия – это сумма всех цифр в дате рождения, а также сумма цифр в получившемся числе» (стр. 2401-2403)
- «Включается и особенно влияет на жизнь человека по достижении им 33 лет» (стр. 2404-2405)

Пример расчёта (стр. 2409-2412):
29.02.1988
2+9+0+2+1+9+8+8=39
3+9=12
1+2=3
ЧД = 3

Исключения (стр. 2414-2418):
- ЧС 1 → ЧД 7 (внутренний конфликт)
- ЧС 3 → ЧД 6 (внутренний конфликт)
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Union


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


def calc_chd(date_input: Union[str, date]) -> int:
    """Рассчитать ЧД по дате рождения.
    
    Алгоритм из «Книги Знаний»:
    1. Суммируем ВСЕ цифры даты рождения
    2. Сворачиваем результат до однозначного числа (1..9)
    
    :param date_input: Дата в формате "dd.mm.yyyy" или объект date
    :return: ЧД (1..9)
    :raises ValueError: при неверном формате даты
    """
    if isinstance(date_input, str):
        try:
            d = datetime.strptime(date_input, "%d.%m.%Y").date()
        except ValueError as e:
            raise ValueError("Ожидается дата в формате dd.mm.yyyy") from e
    elif isinstance(date_input, date):
        d = date_input
    else:
        raise TypeError("Ожидается str (dd.mm.yyyy) или datetime.date")
    
    # Суммируем все цифры даты
    day_str = f"{d.day:02d}"
    month_str = f"{d.month:02d}"
    year_str = f"{d.year:04d}"
    
    total_sum = 0
    for digit in day_str + month_str + year_str:
        total_sum += int(digit)
    
    return _reduce_to_single_digit(total_sum)


def calc_chd_with_exceptions(date_input: Union[str, date], chs: int) -> int:
    """Рассчитать ЧД с учётом исключений для ЧС.
    
    Исключения из «Книги Знаний»:
    - ЧС 1 → ЧД 7 (внутренний конфликт, маленькая смерть)
    - ЧС 3 → ЧД 6 (внутренний конфликт)
    
    :param date_input: Дата в формате "dd.mm.yyyy" или объект date
    :param chs: Число Сознания (1..9)
    :return: ЧД с учётом исключений
    """
    chd = calc_chd(date_input)
    
    # Проверяем исключения
    if chs == 1 and chd == 7:
        # Внутренний конфликт, маленькая смерть
        return 7
    elif chs == 3 and chd == 6:
        # Внутренний конфликт
        return 6
    
    return chd
