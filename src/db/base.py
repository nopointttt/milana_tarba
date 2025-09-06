"""src/db/base.py
Инициализация подключения к БД и фабрики сессий SQLModel.

Примечание: Для миграций используем Alembic (см. ARCHITECTURE.md).
"""
from __future__ import annotations

from typing import Callable

from sqlmodel import SQLModel, Session, create_engine

from src.config import Settings


def _normalize_db_url(url: str) -> str:
    """Если указан префикс postgresql://, заменить на postgresql+psycopg://.

    Это гарантирует использование драйвера psycopg3. Иные схемы не трогаем.
    """
    prefix = "postgresql://"
    if url.startswith(prefix):
        return "postgresql+psycopg://" + url[len(prefix) :]
    return url


def make_engine(settings: Settings):
    """Создать SQLAlchemy Engine для Neon PostgreSQL.

    Ожидаемый формат строки подключения: postgresql+psycopg://USER:PASSWORD@HOST/DB
    """
    connect_args = {}
    db_url = _normalize_db_url(settings.database_url)
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        echo=False,
        connect_args=connect_args,
    )
    return engine


def make_session_factory(engine) -> Callable[[], Session]:
    """Вернуть фабрику сессий SQLModel."""
    def _factory() -> Session:
        return Session(engine)

    return _factory


def init_db(engine) -> None:
    """Создать таблицы при необходимости (для локальной разработки).

    В production используйте Alembic миграции.
    """
    SQLModel.metadata.create_all(engine)
