"""src/db/models.py
ORM-модели (SQLModel) для основных сущностей.
Соответствуют требованиям хранения диалогов и заявок на отчет.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class ReportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_user_id: str = Field(index=True, unique=True, description="ID пользователя в Telegram")
    username: Optional[str] = Field(default=None, description="@username")
    full_name: Optional[str] = Field(default=None, description="Отображаемое имя")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Dialog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dialog_id: int = Field(foreign_key="dialog.id", index=True)
    role: str = Field(description="user|assistant")
    content: str = Field(description="Текст сообщения")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReportRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    # Входные данные от пользователя
    full_name: str = Field(description="Полное имя, предоставленное пользователем")
    birth_date: date = Field(description="Дата рождения (dd.mm.yyyy)")

    # Технические поля
    status: ReportStatus = Field(default=ReportStatus.PENDING)
    result_text: Optional[str] = Field(default=None, description="Готовый текстовый отчет")
    error: Optional[str] = Field(default=None, description="Текст ошибки, если возникла")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NameTransliteration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    original_name: str = Field(description="Имя на исходном алфавите")
    transliterated_name: str = Field(description="Имя, транслитерированное в латиницу")
    confirmed: bool = Field(default=False, description="Подтверждено пользователем")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Memory Bank models
class Memory(SQLModel, table=True):
    """Модель для хранения воспоминаний пользователя"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    
    # Основные поля памяти
    title: str = Field(description="Краткое название воспоминания")
    content: str = Field(description="Содержимое воспоминания")
    memory_type: str = Field(description="Тип воспоминания: personal, preference, context, etc.")
    
    # Метаданные
    importance: int = Field(default=1, description="Важность от 1 до 10")
    tags: Optional[str] = Field(default=None, description="Теги через запятую")
    
    # Временные метки
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: Optional[datetime] = Field(default=None, description="Последний доступ к памяти")
    
    # Связи
    related_memories: Optional[str] = Field(default=None, description="ID связанных воспоминаний через запятую")


class MemoryAccess(SQLModel, table=True):
    """Модель для отслеживания доступа к воспоминаниям"""
    id: Optional[int] = Field(default=None, primary_key=True)
    memory_id: int = Field(foreign_key="memory.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    
    access_type: str = Field(description="Тип доступа: read, create, update, delete")
    context: Optional[str] = Field(default=None, description="Контекст доступа")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
