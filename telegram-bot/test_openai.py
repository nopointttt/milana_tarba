"""test_openai.py
Скрипт для тестирования интеграции с OpenAI.
"""
import asyncio
import sys

# Исправляем проблему с event loop на Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.config import Settings
from src.services.openai_service import OpenAIService
from src.services.analytics.analytics_service import AnalyticsService


async def test_openai_integration():
    """Тестировать интеграцию с OpenAI."""
    print("🤖 Тестирование интеграции с OpenAI...")
    
    try:
        # Загружаем настройки
        settings = Settings.from_env()
        print(f"✅ Настройки загружены (окружение: {settings.environment})")
        
        if not settings.openai_api_key:
            print("❌ OPENAI_API_KEY не задан в окружении")
            return False
        
        # Создаём сервис OpenAI
        openai_service = OpenAIService(
            api_key=settings.openai_api_key,
            assistant_id=settings.openai_assistant_id
        )
        print("✅ OpenAI сервис создан")
        
        # Выполняем тестовый анализ
        analytics_service = AnalyticsService()
        analysis_data = analytics_service.analyze_person(
            birth_date="15.03.1990",
            full_name="Иван Петров"
        )
        print("✅ Анализ выполнен успешно")
        
        # Получаем персонализированный отчёт
        print("🤖 Получаю персонализированный анализ...")
        personalized_report = await openai_service.analyze_person(
            birth_date="15.03.1990",
            full_name="Иван Петров",
            analysis_data=analysis_data
        )
        
        print("✅ Персонализированный анализ получен:")
        print("=" * 50)
        print(personalized_report)
        print("=" * 50)
        
        print("\n🎉 Тест OpenAI прошёл успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Главная функция."""
    success = await test_openai_integration()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
