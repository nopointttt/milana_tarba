"""Тесты для валидации данных пользователей."""
import pytest
from datetime import datetime
import sys
import os

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.analytics.transliteration import validate_name
from services.analytics.analytics_service import AnalyticsService


class TestNameValidation:
    """Тесты валидации имен."""
    
    def test_valid_english_names(self):
        """Тест валидных английских имен."""
        valid_names = ["Ivan", "Maria", "John", "Anna", "David"]
        for name in valid_names:
            assert validate_name(name) == True, f"Имя {name} должно быть валидным"
    
    def test_invalid_names_with_spaces(self):
        """Тест невалидных имен с пробелами."""
        invalid_names = ["Ivan Petrov", "Maria Garcia", "John Smith"]
        for name in invalid_names:
            assert validate_name(name) == False, f"Имя {name} не должно быть валидным"
    
    def test_invalid_cyrillic_names(self):
        """Тест невалидных кириллических имен."""
        invalid_names = ["Иван", "Мария", "Жаслан", "Анна"]
        for name in invalid_names:
            assert validate_name(name) == False, f"Имя {name} не должно быть валидным"
    
    def test_invalid_names_with_numbers(self):
        """Тест невалидных имен с цифрами."""
        invalid_names = ["Ivan123", "Maria1", "John2"]
        for name in invalid_names:
            assert validate_name(name) == False, f"Имя {name} не должно быть валидным"
    
    def test_empty_name(self):
        """Тест пустого имени."""
        assert validate_name("") == False, "Пустое имя не должно быть валидным"
        assert validate_name("   ") == False, "Имя из пробелов не должно быть валидным"


class TestDateValidation:
    """Тесты валидации дат."""
    
    def test_valid_dates(self):
        """Тест валидных дат."""
        valid_dates = ["20.05.1997", "01.01.2000", "31.12.1990"]
        analytics_service = AnalyticsService()
        
        for date_str in valid_dates:
            result = analytics_service.validate_birth_date(date_str)
            assert result == True, f"Дата {date_str} должна быть валидной"
    
    def test_invalid_dates(self):
        """Тест невалидных дат."""
        invalid_dates = ["32.05.1997", "20.13.1997", "20.05.97"]
        analytics_service = AnalyticsService()
        
        for date_str in invalid_dates:
            result = analytics_service.validate_birth_date(date_str)
            assert result == False, f"Дата {date_str} не должна быть валидной"
    
    def test_valid_alternative_date_formats(self):
        """Тест альтернативных валидных форматов дат."""
        valid_dates = ["20/05/1997", "20-05-1997", "20 05 1997"]
        analytics_service = AnalyticsService()
        
        for date_str in valid_dates:
            result = analytics_service.validate_birth_date(date_str)
            assert result == True, f"Дата {date_str} должна быть валидной"
    
    def test_date_normalization(self):
        """Тест нормализации дат."""
        analytics_service = AnalyticsService()
        
        # Тест различных форматов
        test_cases = [
            ("20.05.1997", "20.05.1997"),
            ("20/05/1997", "20.05.1997"),
            ("20-05-1997", "20.05.1997"),
            ("20 05 1997", "20.05.1997"),
        ]
        
        for input_date, expected in test_cases:
            result = analytics_service.normalize_date(input_date)
            assert result == expected, f"Дата {input_date} должна нормализоваться в {expected}"


if __name__ == "__main__":
    pytest.main([__file__])
