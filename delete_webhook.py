"""delete_webhook.py
Скрипт для удаления webhook и настройки бота для polling.
"""
import asyncio
import os
from aiogram import Bot

async def delete_webhook():
    """Удалить webhook и настроить бота для polling."""
    # Читаем токен из .env
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в .env файле")
        return
    
    bot = Bot(token)
    
    try:
        # Удаляем webhook
        print("🔄 Удаляю webhook...")
        await bot.delete_webhook()
        print("✅ Webhook удалён успешно!")
        
        # Проверяем статус
        webhook_info = await bot.get_webhook_info()
        print(f"📊 Статус webhook: {webhook_info.url or 'Не установлен'}")
        
        # Получаем информацию о боте
        bot_info = await bot.get_me()
        print(f"🤖 Бот: @{bot_info.username} ({bot_info.first_name})")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(delete_webhook())
