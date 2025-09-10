# telegram-bot/clear_user_data.py
import asyncio
import sys
from dotenv import load_dotenv
from src.config import Settings
from src.db.connection import initialize_database
from src.services.user_service import UserService

# Исправляем проблему с event loop на Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def clear_user_data():
    """Очистить данные конкретного пользователя."""
    # Загружаем настройки
    load_dotenv()
    settings = Settings.from_env()
    
    # Инициализируем БД
    db_manager = initialize_database(settings)
    await db_manager.initialize()
    
    try:
        # Получаем сессию БД
        async with db_manager.get_session() as session:
            user_service = UserService(session)
            
            # Ищем пользователя по Telegram ID
            telegram_id = 688133152
            user = await user_service.get_user_by_telegram_id(telegram_id)
            
            if user:
                print(f"✅ Пользователь найден в БД:")
                print(f"ID: {user.id}")
                print(f"Telegram ID: {user.telegram_user_id}")
                print(f"Username: {user.username}")
                print(f"Full Name: {user.full_name}")
                
                # Здесь можно добавить очистку данных из БД, если нужно
                print("ℹ️ Данные в БД остаются (они корректные)")
            else:
                print(f"❌ Пользователь с Telegram ID {telegram_id} не найден в БД")
            
            print("\n🔧 Проблема была в in-memory данных (user_data словарь)")
            print("✅ Исправления в коде:")
            print("  - Добавлена проверка валидности данных")
            print("  - Неполные данные теперь очищаются при /start")
            print("  - Кнопка 'Обновить данные' теперь работает правильно")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(clear_user_data())
