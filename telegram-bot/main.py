"""main.py
Точка входа для локальной разработки (polling) и production (webhook).
"""
from __future__ import annotations

import asyncio
import logging
import signal
import sys
import os
from typing import Optional
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# Исправляем проблему с event loop на Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception as e:  # noqa: BLE001
    logging.getLogger(__name__).warning("Could not load .env via python-dotenv: %s", e)

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from src.config import Settings
from src.db.connection import initialize_database
from src.handlers import context_handler, memory_handler


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def setup_sentry(dsn: Optional[str]) -> None:
    if dsn:
        try:
            import sentry_sdk  # type: ignore

            sentry_sdk.init(dsn=dsn, traces_sample_rate=1.0)
        except Exception as e:  # noqa: BLE001
            logging.getLogger(__name__).warning("Sentry init failed: %s", e)


async def setup_bot_commands(bot: Bot) -> None:
    """Устанавливаем команды бота в меню."""
    commands = [
        BotCommand(command="start", description="🏠 Начать работу с ботом"),
        BotCommand(command="menu", description="Показать главное меню"),
        BotCommand(command="chat", description="Обезличенный режим"),
        BotCommand(command="marketing", description="Маркетинговый режим"),
        BotCommand(command="sales", description="Режим продаж"),
        BotCommand(command="update", description="Обновить данные"),
        BotCommand(command="clear", description="Очистить контекст"),
        BotCommand(command="about", description="О боте"),
        BotCommand(command="support", description="Служба заботы"),
    ]
    await bot.set_my_commands(commands)


async def polling_app() -> None:
    settings = Settings.from_env()
    setup_logging()
    setup_sentry(settings.sentry_dsn)

    # Инициализируем базу данных
    db_manager = initialize_database(settings)
    await db_manager.initialize()

    bot = Bot(settings.telegram_bot_token)
    dp = Dispatcher()

    # Устанавливаем команды бота
    await setup_bot_commands(bot)

    # Routers
    dp.include_router(context_handler.router)
    dp.include_router(memory_handler.router)

    # Настройка graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler(signum, frame):
        print(f"\n🛑 Получен сигнал {signum}. Останавливаю бота...")
        shutdown_event.set()
    
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # SIGTERM
    
    try:
        print("🚀 Запускаю бота...")
        print("💡 Для остановки нажмите Ctrl+C")
        
        # Запускаем polling в фоне
        polling_task = asyncio.create_task(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        )
        
        # Ждём сигнала остановки
        await shutdown_event.wait()
        
        print("⏹️ Останавливаю polling...")
        polling_task.cancel()
        
        try:
            await polling_task
        except asyncio.CancelledError:
            pass
        
        print("✅ Бот остановлен корректно")
        
    except Exception as e:
        print(f"❌ Ошибка при работе бота: {e}")
        raise
    finally:
        # Закрываем соединения
        await bot.session.close()
        await db_manager.close()


async def webhook_app() -> web.Application:
    """Создание webhook приложения для production."""
    settings = Settings.from_env()
    
    # Инициализируем базу данных
    await initialize_database()
    
    # Создаем бота и диспетчер
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()
    
    # Регистрируем роутеры
    dp.include_router(context_handler.router)
    dp.include_router(memory_handler.router)
    
    # Создаем webhook приложение
    app = web.Application()
    
    # Настраиваем webhook
    webhook_path = "/webhook"
    webhook_url = os.getenv("WEBHOOK_URL", f"https://your-app.railway.app{webhook_path}")
    
    # Устанавливаем webhook
    await bot.set_webhook(webhook_url)
    print(f"🌐 Webhook установлен: {webhook_url}")
    
    # Настраиваем обработчик
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=webhook_path)
    
    # Добавляем health check
    async def health_check(request):
        return web.Response(text="OK")
    
    app.router.add_get("/health", health_check)
    
    return app

def main():
    """Главная функция с обработкой ошибок."""
    # Проверяем, запускаем ли мы в production (webhook) или локально (polling)
    if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("WEBHOOK_MODE"):
        # Production режим - webhook
        print("🚀 Запуск в production режиме (webhook)")
        try:
            app = asyncio.run(webhook_app())
            web.run_app(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
        except Exception as e:
            print(f"❌ Ошибка webhook сервера: {e}")
            sys.exit(1)
    else:
        # Локальный режим - polling
        print("🏠 Запуск в локальном режиме (polling)")
        try:
            asyncio.run(polling_app())
        except KeyboardInterrupt:
            print("\n👋 До свидания!")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
