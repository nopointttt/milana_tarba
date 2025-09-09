"""Юнит-тесты для расчёта Числа Сознания (ЧС).
Основаны на правилах из файла «Книга Знаний.txt» (стр. 474–488 и 498–501).
"""
from __future__ import annotations

from datetime import date

import pytest

from src.services.analytics.chs import calc_chs, calc_chs_from_day


def test_calc_chs_example_29_returns_2():
    # Пример из книги: 29 -> 2
    assert calc_chs("29.02.2000") == 2


def test_calc_chs_single_digit_days():
    assert calc_chs("01.01.2000") == 1
    assert calc_chs("02.01.2000") == 2
    assert calc_chs("09.01.2000") == 9


def test_calc_chs_reduction_cases():
    # 19 -> 1, 28 -> 1, 31 -> 4
    assert calc_chs("19.01.2000") == 1
    assert calc_chs("28.01.2000") == 1
    assert calc_chs("31.01.2000") == 4


def test_calc_chs_from_day_validation():
    with pytest.raises(ValueError):
        calc_chs_from_day(0)
    with pytest.raises(ValueError):
        calc_chs_from_day(32)


def test_calc_chs_invalid_format_raises_value_error():
    with pytest.raises(ValueError):
        calc_chs("31-01-2000")


def test_calc_chs_wrong_type_raises_type_error():
    with pytest.raises(TypeError):
        calc_chs(123)  # type: ignore[arg-type]
