"""src/services/analytics/matrix.py
Алгоритм построения Матрицы по «Книге Знаний по Цифрологии» (система Миланы Тарба).

Источник (цитаты по файлу «Книга Знаний.txt»):
- «Матрица – какие энергии в тебе заложены» (стр. 464)
- «Шаг 1. Берем дату рождения. Например, если дата рождения: 29.02.1988» (стр. 3342-3343)
- «Шаг 2. Располагаем все цифры из даты рождения в ячейках» (стр. 3344-3347)

Структура матрицы (3x3):
1 2 3
4 5 6  
7 8 9

Правила анализа (стр. 3360-3367):
- 1 цифра = 50% качества
- 2 цифры = 100% качества
- 3 цифры = 150% качества
- 4+ цифр = усиление на спад
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Dict, List, Union


class Matrix:
    """Матрица цифр из даты рождения."""
    
    def __init__(self, date_input: Union[str, date]):
        """Инициализировать матрицу по дате рождения.
        
        :param date_input: Дата в формате "dd.mm.yyyy" или объект date
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
        
        # Извлекаем все цифры из даты
        day_str = f"{d.day:02d}"
        month_str = f"{d.month:02d}"
        year_str = f"{d.year:04d}"
        
        all_digits = []
        for digit in day_str + month_str + year_str:
            digit_int = int(digit)
            if digit_int != 0:  # Исключаем 0 согласно «Книге Знаний»
                all_digits.append(digit_int)
        
        # Подсчитываем количество каждой цифры
        self.digit_counts = Counter(all_digits)
        
        # Создаём матрицу 3x3
        self.matrix = self._build_matrix()
    
    def _build_matrix(self) -> List[List[int]]:
        """Построить матрицу 3x3 с цифрами из даты рождения.
        
        Структура:
        1 2 3
        4 5 6
        7 8 9
        """
        matrix = [[0 for _ in range(3)] for _ in range(3)]
        
        # Заполняем матрицу цифрами из даты
        for digit, count in self.digit_counts.items():
            if digit == 0:
                continue  # 0 не имеет позиции в матрице
            
            # Определяем позицию в матрице (1-9)
            row = (digit - 1) // 3
            col = (digit - 1) % 3
            
            if 0 <= row < 3 and 0 <= col < 3:
                matrix[row][col] = count
        
        return matrix
    
    def get_digit_strength(self, digit: int) -> str:
        """Получить силу цифры в матрице.
        
        :param digit: Цифра 1-9
        :return: Описание силы ("отсутствует", "50%", "100%", "150%", "усиление на спад")
        """
        if digit < 1 or digit > 9:
            return "неверная цифра"
        
        count = self.digit_counts.get(digit, 0)
        
        if count == 0:
            return "отсутствует"
        elif count == 1:
            return "50%"
        elif count == 2:
            return "100%"
        elif count == 3:
            return "150%"
        else:
            return "усиление на спад"
    
    def get_missing_digits(self) -> List[int]:
        """Получить список отсутствующих цифр в матрице.
        
        :return: Список цифр 1-9, которых нет в дате рождения
        """
        missing = []
        for digit in range(1, 10):
            if self.digit_counts.get(digit, 0) == 0:
                missing.append(digit)
        return missing
    
    def get_strong_digits(self) -> List[int]:
        """Получить список сильных цифр (100% и выше).
        
        :return: Список цифр с силой 100% и выше
        """
        strong = []
        for digit in range(1, 10):
            count = self.digit_counts.get(digit, 0)
            if count >= 2:
                strong.append(digit)
        return strong
    
    def get_weak_digits(self) -> List[int]:
        """Получить список слабых цифр (50%).
        
        :return: Список цифр с силой 50%
        """
        weak = []
        for digit in range(1, 10):
            count = self.digit_counts.get(digit, 0)
            if count == 1:
                weak.append(digit)
        return weak
    
    def analyze_energies(self) -> Dict[str, any]:
        """Проанализировать энергии в матрице.
        
        :return: Словарь с анализом энергий
        """
        return {
            "matrix": self.matrix,
            "digit_counts": dict(self.digit_counts),
            "missing_digits": self.get_missing_digits(),
            "strong_digits": self.get_strong_digits(),
            "weak_digits": self.get_weak_digits(),
            "analysis": self._get_energy_analysis()
        }
    
    def _get_energy_analysis(self) -> str:
        """Получить текстовый анализ энергий матрицы.
        
        :return: Описание энергий в матрице
        """
        missing = self.get_missing_digits()
        strong = self.get_strong_digits()
        weak = self.get_weak_digits()
        
        analysis_parts = []
        
        if strong:
            analysis_parts.append(f"Сильные энергии: {', '.join(map(str, strong))} (100% и выше)")
        
        if weak:
            analysis_parts.append(f"Слабые энергии: {', '.join(map(str, weak))} (50%)")
        
        if missing:
            analysis_parts.append(f"Отсутствующие энергии: {', '.join(map(str, missing))}")
        
        return "; ".join(analysis_parts) if analysis_parts else "Сбалансированная матрица"


def build_matrix(date_input: Union[str, date]) -> Matrix:
    """Построить матрицу по дате рождения.
    
    :param date_input: Дата в формате "dd.mm.yyyy" или объект date
    :return: Объект Matrix
    """
    return Matrix(date_input)
