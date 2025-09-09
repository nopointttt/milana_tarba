"""tests/test_analytics_algorithms.py
Unit-тесты для алгоритмов расчётов по «Книге Знаний по Цифрологии».

Тестируем все ключевые алгоритмы с эталонными кейсами из «Книги Знаний».
"""
import pytest
from datetime import date

from src.services.analytics.chs import calc_chs, calc_chs_from_day
from src.services.analytics.chd import calc_chd, calc_chd_with_exceptions
from src.services.analytics.matrix import Matrix, build_matrix
from src.services.analytics.name_number import calc_name_number, get_name_interpretation
from src.services.analytics.transliteration import (
    transliterate_cyrillic_to_latin, 
    is_cyrillic_text, 
    is_latin_text,
    normalize_name_for_calculation
)


class TestChs:
    """Тесты для Числа Сознания (ЧС)."""
    
    def test_chs_from_day_examples(self):
        """Тестируем примеры из «Книги Знаний»."""
        # Пример из книги: 29 (февраля) 2+9=11=1+1=2
        assert calc_chs_from_day(29) == 2
        
        # Другие примеры
        assert calc_chs_from_day(1) == 1
        assert calc_chs_from_day(15) == 6  # 1+5=6
        assert calc_chs_from_day(31) == 4  # 3+1=4
    
    def test_chs_from_date_string(self):
        """Тестируем расчёт ЧС из строки даты."""
        assert calc_chs("29.02.1988") == 2
        assert calc_chs("15.03.1990") == 6
        assert calc_chs("01.01.2000") == 1
    
    def test_chs_from_date_object(self):
        """Тестируем расчёт ЧС из объекта date."""
        d = date(1988, 2, 29)
        assert calc_chs(d) == 2
        
        d = date(1990, 3, 15)
        assert calc_chs(d) == 6
    
    def test_chs_invalid_input(self):
        """Тестируем обработку неверного ввода."""
        with pytest.raises(ValueError, match="Ожидается дата в формате dd.mm.yyyy"):
            calc_chs("29-02-1988")
        
        with pytest.raises(ValueError, match="День месяца должен быть в диапазоне 1..31"):
            calc_chs_from_day(32)
        
        with pytest.raises(TypeError):
            calc_chs(123)


class TestChd:
    """Тесты для Числа Действия (ЧД)."""
    
    def test_chd_example_from_book(self):
        """Тестируем пример из «Книги Знаний»: 29.02.1988."""
        # 2+9+0+2+1+9+8+8=39, 3+9=12, 1+2=3
        assert calc_chd("29.02.1988") == 3
        assert calc_chd(date(1988, 2, 29)) == 3
    
    def test_chd_other_examples(self):
        """Тестируем другие примеры."""
        # 15.03.1990: 1+5+0+3+1+9+9+0 = 28, 2+8 = 10, 1+0 = 1
        assert calc_chd("15.03.1990") == 1
        
        # 01.01.2000: 0+1+0+1+2+0+0+0 = 4
        assert calc_chd("01.01.2000") == 4
    
    def test_chd_with_exceptions(self):
        """Тестируем ЧД с исключениями для ЧС."""
        # ЧС 1 → ЧД 7 (внутренний конфликт)
        chd = calc_chd_with_exceptions("01.01.2000", 1)  # ЧД будет 3, но ЧС 1
        # Нужно найти дату, где ЧС=1 и ЧД=7
        # ЧС=1: день 1, 10, 19, 28
        # ЧД=7: сумма цифр даты должна дать 7
        # Например: 19.01.2000 -> ЧС=1 (1+9=10, 1+0=1), ЧД=7 (1+9+0+1+2+0+0+0=13, 1+3=4... нет)
        # 19.01.2000 -> 1+9+0+1+2+0+0+0 = 13 -> 1+3 = 4
        # Попробуем 19.01.1999 -> 1+9+0+1+1+9+9+9 = 39 -> 3+9 = 12 -> 1+2 = 3
        # 19.01.1988 -> 1+9+0+1+1+9+8+8 = 37 -> 3+7 = 10 -> 1+0 = 1
        # 19.01.1977 -> 1+9+0+1+1+9+7+7 = 35 -> 3+5 = 8
        # 19.01.1966 -> 1+9+0+1+1+9+6+6 = 33 -> 3+3 = 6
        # 19.01.1955 -> 1+9+0+1+1+9+5+5 = 31 -> 3+1 = 4
        # 19.01.1944 -> 1+9+0+1+1+9+4+4 = 29 -> 2+9 = 11 -> 1+1 = 2
        # 19.01.1933 -> 1+9+0+1+1+9+3+3 = 27 -> 2+7 = 9
        # 19.01.1922 -> 1+9+0+1+1+9+2+2 = 25 -> 2+5 = 7 ✓
        
        chd = calc_chd_with_exceptions("19.01.1922", 1)  # ЧС=1, ЧД=7
        assert chd == 7  # Должно остаться 7 из-за исключения
        
        # ЧС 3 → ЧД 6 (внутренний конфликт)
        # Найдём дату где ЧС=3 и ЧД=6
        # ЧС=3: день 3, 12, 21, 30
        # 21.01.1999 -> ЧС=3 (2+1=3), ЧД=6 (2+1+0+1+1+9+9+9=32, 3+2=5... нет)
        # 21.01.1988 -> 2+1+0+1+1+9+8+8=30, 3+0=3... нет
        # 21.01.1977 -> 2+1+0+1+1+9+7+7=28, 2+8=10, 1+0=1... нет
        # 21.01.1966 -> 2+1+0+1+1+9+6+6=26, 2+6=8... нет
        # 21.01.1955 -> 2+1+0+1+1+9+5+5=24, 2+4=6 ✓
        
        chd = calc_chd_with_exceptions("21.01.1955", 3)  # ЧС=3, ЧД=6
        assert chd == 6  # Должно остаться 6 из-за исключения
    
    def test_chd_invalid_input(self):
        """Тестируем обработку неверного ввода."""
        with pytest.raises(ValueError, match="Ожидается дата в формате dd.mm.yyyy"):
            calc_chd("29-02-1988")


class TestMatrix:
    """Тесты для Матрицы."""
    
    def test_matrix_example_from_book(self):
        """Тестируем пример из «Книги Знаний»: 29.02.1988."""
        matrix = Matrix("29.02.1988")
        
        # Ожидаемые цифры: 2, 9, 0, 2, 1, 9, 8, 8
        # Исключаем 0, получаем: 2, 9, 2, 1, 9, 8, 8
        # Подсчёт: 1=1, 2=2, 8=2, 9=2
        expected_counts = {1: 1, 2: 2, 8: 2, 9: 2}
        assert dict(matrix.digit_counts) == expected_counts
        
        # Проверяем силы цифр
        assert matrix.get_digit_strength(1) == "50%"
        assert matrix.get_digit_strength(2) == "100%"
        assert matrix.get_digit_strength(8) == "100%"
        assert matrix.get_digit_strength(9) == "100%"
        assert matrix.get_digit_strength(3) == "отсутствует"
    
    def test_matrix_analysis(self):
        """Тестируем анализ матрицы."""
        matrix = Matrix("29.02.1988")
        analysis = matrix.analyze_energies()
        
        assert analysis["missing_digits"] == [3, 4, 5, 6, 7]
        assert set(analysis["strong_digits"]) == {2, 8, 9}
        assert analysis["weak_digits"] == [1]
    
    def test_matrix_other_examples(self):
        """Тестируем другие примеры матриц."""
        matrix = Matrix("15.03.1990")
        # Цифры: 1, 5, 0, 3, 1, 9, 9, 0
        # Исключаем 0: 1, 5, 3, 1, 9, 9
        # Подсчёт: 1=2, 3=1, 5=1, 9=2
        expected_counts = {1: 2, 3: 1, 5: 1, 9: 2}
        assert dict(matrix.digit_counts) == expected_counts


class TestNameNumber:
    """Тесты для Числа Имени."""
    
    def test_name_number_example_from_book(self):
        """Тестируем пример из «Книги Знаний»: Milana = 6."""
        assert calc_name_number("Milana") == 6
        # Проверим: M=4, I=1, L=3, A=1, N=5, A=1
        # 4+1+3+1+5+1 = 15, 1+5 = 6 ✓
    
    def test_name_number_other_examples(self):
        """Тестируем другие примеры имён."""
        # IVAN: I=1, V=6, A=1, N=5 = 1+6+1+5 = 13 -> 1+3 = 4
        assert calc_name_number("IVAN") == 4
        
        # ANNA: A=1, N=5, N=5, A=1 = 1+5+5+1 = 12 -> 1+2 = 3
        assert calc_name_number("ANNA") == 3
    
    def test_name_interpretation(self):
        """Тестируем интерпретации чисел имён."""
        assert "Лидерство" in get_name_interpretation(1)
        assert "Дипломатия" in get_name_interpretation(2)
        assert "Творчество" in get_name_interpretation(3)
    
    def test_name_number_invalid_input(self):
        """Тестируем обработку неверного ввода."""
        with pytest.raises(ValueError, match="Имя не может быть пустым"):
            calc_name_number("")
        
        with pytest.raises(ValueError, match="Недопустимый символ"):
            calc_name_number("Иван123")


class TestTransliteration:
    """Тесты для транслитерации."""
    
    def test_transliteration_examples(self):
        """Тестируем примеры транслитерации."""
        assert transliterate_cyrillic_to_latin("Иван") == "IVAN"
        assert transliterate_cyrillic_to_latin("Петров") == "PETROV"
        assert transliterate_cyrillic_to_latin("Анна") == "ANNA"
        assert transliterate_cyrillic_to_latin("Мария") == "MARIYA"
    
    def test_text_detection(self):
        """Тестируем определение типа текста."""
        assert is_cyrillic_text("Иван") == True
        assert is_cyrillic_text("IVAN") == False
        assert is_latin_text("IVAN") == True
        assert is_latin_text("Иван") == False
    
    def test_name_normalization(self):
        """Тестируем нормализацию имён."""
        assert normalize_name_for_calculation("Иван") == "IVAN"
        assert normalize_name_for_calculation("IVAN") == "IVAN"
        assert normalize_name_for_calculation("ivan") == "IVAN"
        
        # Проверяем, что имена с цифрами отклоняются
        with pytest.raises(ValueError, match="только кириллические или латинские буквы"):
            normalize_name_for_calculation("Иван123")
        
        with pytest.raises(ValueError, match="только кириллические или латинские буквы"):
            normalize_name_for_calculation("Ivan123")


class TestIntegration:
    """Интеграционные тесты для полного анализа."""
    
    def test_full_analysis_example(self):
        """Тестируем полный анализ на примере из книги."""
        # Данные: 29.02.1988, Milana
        birth_date = "29.02.1988"
        name = "Milana"
        
        # ЧС = 2 (29 -> 2+9=11 -> 1+1=2)
        chs = calc_chs(birth_date)
        assert chs == 2
        
        # ЧД = 3 (2+9+0+2+1+9+8+8=39 -> 3+9=12 -> 1+2=3)
        chd = calc_chd(birth_date)
        assert chd == 3
        
        # Число Имени = 6 (M=4, I=1, L=3, A=1, N=5, A=1 = 15 -> 6)
        name_number = calc_name_number(name)
        assert name_number == 6
        
        # Матрица
        matrix = Matrix(birth_date)
        assert matrix.digit_counts[2] == 2  # Двойка встречается 2 раза
        assert matrix.digit_counts[9] == 2  # Девятка встречается 2 раза
