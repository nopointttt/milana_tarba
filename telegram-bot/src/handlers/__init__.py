"""src/handlers/__init__.py
Инициализация хендлеров.
"""
from .context_handler import router as context_router

# Экспортируем главный роутер
start_router = context_router

# Все роутеры для подключения
__all__ = ['context_router']