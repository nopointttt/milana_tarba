"""Тесты для OpenAI интеграции."""
import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Добавляем путь к src
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.openai_context_service import OpenAIContextService


class TestOpenAIContextService:
    """Тесты для OpenAI контекстного сервиса."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_api_key = "test-api-key"
        self.mock_db_session = Mock()
        self.service = OpenAIContextService(
            api_key=self.mock_api_key,
            db_session=self.mock_db_session
        )
    
    def test_initialization(self):
        """Тест инициализации сервиса."""
        assert self.service.client is not None
        assert self.service.functions is not None
        assert self.service.system_prompt is not None
    
    def test_system_prompt_generation(self):
        """Тест генерации системного промпта."""
        prompt = self.service._get_system_prompt()
        
        # Проверяем, что промпт содержит ключевые элементы
        assert "Миланы Тарба" in prompt
        assert "цифрологии" in prompt
        assert "ЧС" in prompt
        assert "ЧД" in prompt
        assert "Матрица" in prompt
        assert "ФОРМАТИРОВАНИЕ" in prompt
    
    @pytest.mark.asyncio
    async def test_process_message_success(self):
        """Тест успешной обработки сообщения."""
        # Настраиваем мок
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Тестовый ответ"
        mock_response.choices[0].message.tool_calls = None

        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        self.service.client = mock_client

        # Тестируем
        result = await self.service.process_message(
            user_message="Тестовое сообщение",
            user_id=123,
            context=[]
        )

        assert result == "Тестовый ответ"
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_message_with_tool_calls(self):
        """Тест обработки сообщения с вызовом функций."""
        # Настраиваем мок для первого вызова
        mock_response1 = Mock()
        mock_response1.choices = [Mock()]
        mock_response1.choices[0].message = Mock()
        mock_response1.choices[0].message.content = None
        mock_response1.choices[0].message.tool_calls = [Mock()]
        mock_response1.choices[0].message.tool_calls[0].function = Mock()
        mock_response1.choices[0].message.tool_calls[0].function.name = "test_function"
        mock_response1.choices[0].message.tool_calls[0].function.arguments = '{"test": "value"}'

        # Настраиваем мок для второго вызова
        mock_response2 = Mock()
        mock_response2.choices = [Mock()]
        mock_response2.choices[0].message = Mock()
        mock_response2.choices[0].message.content = "Ответ после вызова функции"

        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(side_effect=[mock_response1, mock_response2])
        self.service.client = mock_client

        # Тестируем
        result = await self.service.process_message(
            user_message="Тестовое сообщение",
            user_id=123,
            context=[]
        )

        assert result == "Ответ после вызова функции"
        assert mock_client.chat.completions.create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_process_message_error_handling(self):
        """Тест обработки ошибок."""
        # Мокаем клиент для вызова исключения
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        self.service.client = mock_client

        # Тестируем
        result = await self.service.process_message(
            user_message="Тестовое сообщение",
            user_id=123,
            context=[]
        )

        assert "Извините, произошла ошибка" in result


class TestOpenAIFunctions:
    """Тесты для OpenAI функций."""
    
    def test_function_schemas(self):
        """Тест схем функций."""
        from services.openai_functions import OpenAIFunctions
        
        # Проверяем, что класс существует
        assert OpenAIFunctions is not None
        assert hasattr(OpenAIFunctions, 'get_analytics_by_user_id')
        assert hasattr(OpenAIFunctions, 'calculate_analytics')
        assert hasattr(OpenAIFunctions, 'save_analytics')
    
    def test_function_schemas_structure(self):
        """Тест структуры схем функций."""
        from services.openai_functions import OpenAIFunctions
        
        # Создаем экземпляр для проверки методов
        functions = OpenAIFunctions(Mock())
        
        # Проверяем, что методы существуют
        assert hasattr(functions, 'get_analytics_by_user_id')
        assert hasattr(functions, 'calculate_analytics')
        assert hasattr(functions, 'save_analytics')


if __name__ == "__main__":
    pytest.main([__file__])
