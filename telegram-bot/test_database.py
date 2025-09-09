"""test_database.py
Скрипт для тестирования подключения к базе данных.
"""
import asyncio
import sys
from datetime import date

# Исправляем проблему с event loop на Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.config import Settings
from src.db.connection import initialize_database
from src.db.models import User, ReportRequest, ReportStatus
from src.services.analytics.analytics_service import AnalyticsService
from src.services.user_service import UserService
from src.services.analytics_storage import AnalyticsStorageService


async def test_database_connection():
    """Тестировать подключение к базе данных."""
    print("🔍 Тестирование подключения к базе данных...")
    
    try:
        # Загружаем настройки
        settings = Settings.from_env()
        print(f"✅ Настройки загружены (окружение: {settings.environment})")
        
        # Инициализируем БД
        db_manager = initialize_database(settings)
        await db_manager.initialize()
        print("✅ Подключение к базе данных установлено")
        
        # Тестируем создание пользователя
        async with db_manager.get_session() as session:
            user_service = UserService(session)
            
            # Создаём тестового пользователя
            test_user = await user_service.get_or_create_user(
                telegram_user_id=12345,
                username="test_user",
                full_name="Test User"
            )
            
            # Коммитим пользователя, чтобы получить ID
            await session.commit()
            await session.refresh(test_user)
            
            print(f"✅ Пользователь создан: ID={test_user.id}, Telegram ID={test_user.telegram_user_id}")
            
            # Тестируем аналитику
            analytics_service = AnalyticsService()
            storage_service = AnalyticsStorageService(session)
            
            # Выполняем тестовый анализ
            analysis_result = analytics_service.analyze_person(
                birth_date="15.03.1990",
                full_name="Иван Петров"
            )
            print("✅ Анализ выполнен успешно")
            
            # Сохраняем результат в БД
            report = await storage_service.save_analysis_result(
                user_id=test_user.id,
                full_name="Иван Петров",
                birth_date=date(1990, 3, 15),
                analysis_result=analysis_result
            )
            print(f"✅ Результат сохранён в БД: Report ID={report.id}")
            
            # Проверяем, что можем получить сохранённый анализ
            saved_analyses = await storage_service.get_user_analyses(test_user.id, limit=1)
            if saved_analyses:
                print(f"✅ Получен сохранённый анализ: {saved_analyses[0].status}")
            else:
                print("❌ Не удалось получить сохранённый анализ")
        
        print("\n🎉 Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db_manager' in locals():
            await db_manager.close()
    
    return True


async def main():
    """Главная функция."""
    success = await test_database_connection()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
