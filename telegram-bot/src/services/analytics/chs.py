"""src/services/analytics/chs.py
Алгоритм расчёта Числа Сознания (ЧС) по «Книге Знаний по Цифрологии» (система Миланы Тарба).

Источник (цитаты по файлу «Книга Знаний.txt»):
- «День рождения (число без указания месяца и года рождения) – это ЧИСЛО СОЗНАНИЯ» (стр. 474–488)
- «Число Сознания – это сумма чисел дня в дате рождения, когда ты родился. \nНапример: 29 (февраля) 2+9=11=1+1=2.» (стр. 498–501)

Правило: берём ТОЛЬКО день месяца и сворачиваем сумму цифр до однозначного числа 1..9.
Исключения (мастер-числа 11/22 и т.п.) не сохраняем — как показано в примере 29→11→2.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Iterable, Union


def _digit_sum(n: int) -> int:
    """Вернуть сумму цифр числа n (по модулю)."""
    n = abs(n)
    s = 0
    while n:
        s += n % 10
        n //= 10
    return s


def _reduce_to_single_digit(n: int) -> int:
    """Свернуть число до однозначного (1..9) повторной суммой цифр.

    Примечание: Число дня всегда 1..31, поэтому результат всегда в диапазоне 1..9.
    """
    if n <= 0:
        raise ValueError("Ожидалось положительное число дня")
    while n > 9:
        n = _digit_sum(n)
    return n


def calc_chs_from_day(day: int) -> int:
    """Рассчитать ЧС по дню месяца.

    :param day: День месяца (1..31)
    :return: ЧС (1..9)
    :raises ValueError: если день вне диапазона
    """
    if not (1 <= day <= 31):
        raise ValueError("День месяца должен быть в диапазоне 1..31")
    return _reduce_to_single_digit(day)


def calc_chs(date_input: Union[str, date]) -> int:
    """Рассчитать ЧС по дате рождения.

    Принимает дату формата "dd.mm.yyyy" или объект date. Берёт только день месяца и
    сворачивает до 1..9 согласно «Книге Знаний».
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

    return calc_chs_from_day(d.day)
