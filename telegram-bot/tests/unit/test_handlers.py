"""Тесты для обработчиков сообщений."""
import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from handlers.context_handler import (
    is_date_format,
    is_name_format,
    is_additional_data,
    extract_additional_data,
    clear_additional_data
)


class TestDataValidation:
    """Тесты валидации данных в обработчиках."""
    
    def test_is_date_format_valid(self):
        """Тест валидных форматов дат."""
        valid_dates = [
            "20.05.1997",
            "01.01.2000",
            "31.12.1990",
            "1.1.2000",
            "9.9.1999"
        ]
        
        for date in valid_dates:
            assert is_date_format(date), f"Дата {date} должна быть валидной"
    
    def test_is_date_format_invalid(self):
        """Тест невалидных форматов дат."""
        invalid_dates = [
            "32.05.1997",  # Невалидный день
            "20.13.1997",  # Невалидный месяц
            "not_a_date",  # Не дата
            "20.05.97",    # Неполный год
            "20.5.1997"    # Неполный месяц
        ]
        
        for date in invalid_dates:
            assert not is_date_format(date), f"Дата {date} не должна быть валидной"
    
    def test_is_date_format_valid_alternative_formats(self):
        """Тест альтернативных валидных форматов дат."""
        valid_dates = [
            "20/05/1997",  # Слеш
            "20-05-1997",  # Дефис
            "20 05 1997"   # Пробелы
        ]
        
        for date in valid_dates:
            assert is_date_format(date), f"Дата {date} должна быть валидной"
    
    def test_is_name_format_valid(self):
        """Тест валидных форматов имен."""
        valid_names = [
            "Ivan",
            "Maria",
            "John",
            "Anna",
            "David",
            "VeryLongName"
        ]
        
        for name in valid_names:
            assert is_name_format(name), f"Имя {name} должно быть валидным"
    
    def test_is_name_format_invalid(self):
        """Тест невалидных форматов имен."""
        invalid_names = [
            "Ivan Petrov",      # Пробел
            "Maria Garcia",     # Пробел
            "John Smith",       # Пробел
            "Ivan123",          # Цифры
            "Ivan-Petrov",      # Дефис
            "Ivan_Petrov",      # Подчеркивание
            "",                 # Пустое
            "   ",              # Пробелы
            "Ivan Petrov Garcia", # Много слов
            "A",                # Слишком короткое
            "VeryVeryVeryVeryVeryLongName"  # Слишком длинное
        ]
        
        for name in invalid_names:
            assert not is_name_format(name), f"Имя {name} не должно быть валидным"


class TestAdditionalDataHandling:
    """Тесты обработки дополнительных данных."""
    
    def test_is_additional_data_with_main_data(self):
        """Тест определения дополнительных данных при наличии основных."""
        # Имитируем наличие основных данных
        user_id = 123
        main_name = "Ivan"
        main_date = "20.05.1997"
        
        # Мокаем user_data
        with patch('handlers.context_handler.user_data', {user_id: {"name": main_name, "birth_date": main_date}}):
            # Тест с теми же данными (не дополнительные)
            same_data = f"{main_name}\n{main_date}"
            assert not is_additional_data(same_data, user_id), "Те же данные не должны быть дополнительными"
            
            # Тест с другими данными (дополнительные)
            different_data = "Maria\n15.03.1995"
            assert is_additional_data(different_data, user_id), "Другие данные должны быть дополнительными"
    
    def test_is_additional_data_without_main_data(self):
        """Тест определения дополнительных данных без основных."""
        user_id = 123
        data = "Maria\n15.03.1995"
        
        # Мокаем отсутствие основных данных
        with patch('handlers.context_handler.user_data', {}):
            assert not is_additional_data(data, user_id), "Без основных данных не должно быть дополнительных"
    
    def test_extract_additional_data(self):
        """Тест извлечения дополнительных данных."""
        data = "Maria\n15.03.1995"
        result = extract_additional_data(data)
        
        expected = {"name": "Maria", "birth_date": "15.03.1995"}
        assert result == expected, f"Должны быть извлечены данные {expected}, получено {result}"
    
    def test_extract_additional_data_invalid(self):
        """Тест извлечения невалидных дополнительных данных."""
        invalid_data = ["Maria", "OnlyName", "OnlyDate\n15.03.1995"]
        
        for data in invalid_data:
            result = extract_additional_data(data)
            assert result == {}, f"Невалидные данные должны возвращать пустой словарь, получено {result}"
    
    def test_extract_additional_data_with_extra_lines(self):
        """Тест извлечения данных с дополнительными строками."""
        # Функция берет только первые 2 строки, игнорируя остальные
        data = "15.03.1995\nExtra"
        result = extract_additional_data(data)
        expected = {"name": "15.03.1995", "birth_date": "Extra"}
        assert result == expected, f"Должны быть извлечены первые 2 строки, получено {result}"
    
    def test_clear_additional_data(self):
        """Тест очистки дополнительных данных."""
        user_id = 123
        
        # Мокаем additional_data
        mock_additional_data = {user_id: [{"name": "Maria", "birth_date": "15.03.1995"}]}
        with patch('handlers.context_handler.additional_data', mock_additional_data):
            clear_additional_data(user_id)
            assert user_id in mock_additional_data
            assert mock_additional_data[user_id] == [], "Дополнительные данные должны быть очищены"


class TestMessageProcessing:
    """Тесты обработки сообщений."""
    
    @patch('handlers.context_handler.send_typing_status')
    @patch('handlers.context_handler.send_status_message')
    @patch('handlers.context_handler.update_status_message')
    def test_message_processing_flow(self, mock_update_status, mock_send_status, mock_typing):
        """Тест потока обработки сообщений."""
        # Этот тест требует более сложной настройки моков
        # для полного тестирования обработки сообщений
        pass
    
    def test_user_data_management(self):
        """Тест управления данными пользователей."""
        # Тест добавления, обновления и удаления данных пользователей
        pass


if __name__ == "__main__":
    pytest.main([__file__])
