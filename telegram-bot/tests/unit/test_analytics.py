"""Тесты для расчетов аналитики."""
import pytest
import sys
import os
from datetime import datetime

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.analytics.chs import calc_chs
from services.analytics.chd import calc_chd
from services.analytics.matrix import build_matrix
from services.analytics.name_number import calc_name_number


class TestCHSCalculation:
    """Тесты расчета ЧС (Числа Сознания)."""
    
    def test_chs_calculation(self):
        """Тест расчета ЧС."""
        # Тест с известной датой
        birth_date = datetime(1997, 5, 20)
        chs = calc_chs(birth_date)
        assert chs == 2, f"ЧС для 20.05.1997 должно быть 2, получено {chs}"
    
    def test_chs_single_digit(self):
        """Тест ЧС для однозначного числа."""
        birth_date = datetime(1990, 1, 1)
        chs = calc_chs(birth_date)
        assert chs == 1, f"ЧС для 01.01.1990 должно быть 1, получено {chs}"
    
    def test_chs_master_numbers(self):
        """Тест ЧС для мастер-чисел."""
        # 11.11.1991 = 1+1 = 2 (только день)
        birth_date = datetime(1991, 11, 11)
        chs = calc_chs(birth_date)
        assert chs == 2, f"ЧС для 11.11.1991 должно быть 2, получено {chs}"


class TestCHDCalculation:
    """Тесты расчета ЧД (Числа Действия)."""
    
    def test_chd_calculation(self):
        """Тест расчета ЧД."""
        birth_date = datetime(1997, 5, 20)
        chd = calc_chd(birth_date)
        assert chd == 6, f"ЧД для 20.05.1997 должно быть 6, получено {chd}"
    
    def test_chd_single_digit(self):
        """Тест ЧД для однозначного числа."""
        birth_date = datetime(1990, 1, 1)
        chd = calc_chd(birth_date)
        assert chd == 3, f"ЧД для 01.01.1990 должно быть 3, получено {chd}"


class TestMatrixCalculation:
    """Тесты расчета Матрицы."""
    
    def test_matrix_calculation(self):
        """Тест расчета Матрицы."""
        birth_date = datetime(1997, 5, 20)
        matrix = build_matrix(birth_date)
        
        # Проверяем, что матрица - это объект Matrix
        assert hasattr(matrix, '__dict__'), "Матрица должна быть объектом"
        
        # Проверяем, что матрица содержит необходимые атрибуты
        assert hasattr(matrix, 'digit_counts'), "Матрица должна содержать digit_counts"
        assert hasattr(matrix, 'matrix'), "Матрица должна содержать matrix"
        assert hasattr(matrix, 'get_digit_strength'), "Матрица должна содержать get_digit_strength"
        assert hasattr(matrix, 'get_missing_digits'), "Матрица должна содержать get_missing_digits"


class TestNameNumberCalculation:
    """Тесты расчета Числа Имени."""
    
    def test_name_number_calculation(self):
        """Тест расчета Числа Имени."""
        name = "Ivan"
        name_number = calc_name_number(name)
        assert name_number == 4, f"Число имени Ivan должно быть 4, получено {name_number}"
    
    def test_name_number_different_names(self):
        """Тест расчета для разных имен."""
        test_cases = [
            ("Anna", 3),  # A=1, N=5, N=5, A=1 → 1+5+5+1=12 → 1+2=3
            ("David", 7), # D=4, A=1, V=6, I=1, D=4 → 4+1+6+1+4=16 → 1+6=7
            ("Maria", 9), # M=4, A=1, R=2, I=1, A=1 → 4+1+2+1+1=9 → 9
        ]
        
        for name, expected in test_cases:
            result = calc_name_number(name)
            assert result == expected, f"Число имени {name} должно быть {expected}, получено {result}"


class TestAnalyticsIntegration:
    """Интеграционные тесты аналитики."""
    
    def test_full_analysis(self):
        """Тест полного анализа."""
        birth_date = datetime(1997, 5, 20)
        name = "Ivan"
        
        chs = calc_chs(birth_date)
        chd = calc_chd(birth_date)
        matrix = build_matrix(birth_date)
        name_number = calc_name_number(name)
        
        # Проверяем, что все расчеты выполнены
        assert chs is not None, "ЧС должно быть рассчитано"
        assert chd is not None, "ЧД должно быть рассчитано"
        assert matrix is not None, "Матрица должна быть рассчитана"
        assert name_number is not None, "Число имени должно быть рассчитано"
        
        # Проверяем типы данных
        assert isinstance(chs, int), "ЧС должно быть целым числом"
        assert isinstance(chd, int), "ЧД должно быть целым числом"
        assert hasattr(matrix, '__dict__'), "Матрица должна быть объектом"
        assert isinstance(name_number, int), "Число имени должно быть целым числом"


if __name__ == "__main__":
    pytest.main([__file__])
