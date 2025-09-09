"""src/db/connection.py
Управление подключением к базе данных.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import Settings


class DatabaseManager:
    """Менеджер подключения к базе данных."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.engine: AsyncEngine | None = None
        self.session_factory: sessionmaker[AsyncSession] | None = None
    
    async def initialize(self) -> None:
        """Инициализация подключения к базе данных."""
        # Создаём асинхронный движок
        self.engine = create_async_engine(
            self.settings.database_url,
            echo=self.settings.environment == "development",  # Логируем SQL в dev
            future=True,
        )
        
        # Создаём фабрику сессий
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    async def close(self) -> None:
        """Закрытие подключения к базе данных."""
        if self.engine:
            await self.engine.dispose()
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Получить сессию базы данных."""
        if not self.session_factory:
            raise RuntimeError("База данных не инициализирована. Вызовите initialize()")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Глобальный экземпляр менеджера БД
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """Получить глобальный экземпляр менеджера БД."""
    if _db_manager is None:
        raise RuntimeError("Менеджер БД не инициализирован")
    return _db_manager


def initialize_database(settings: Settings) -> DatabaseManager:
    """Инициализировать глобальный менеджер БД."""
    global _db_manager
    _db_manager = DatabaseManager(settings)
    return _db_manager


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Получить сессию БД (удобная функция для dependency injection)."""
    async with get_db_manager().get_session() as session:
        yield session
