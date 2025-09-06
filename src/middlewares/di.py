"""src/middlewares/di.py
DI middleware для Aiogram 3.x. Внедряет сессию БД и OpenAI клиента в хендлеры.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from sqlmodel import Session

from src.services.openai_client import OpenAIClient


class DIMiddleware(BaseMiddleware):
    """Простой DI-мидлвар для прокидывания зависимостей в data."""

    def __init__(self, session_factory: Callable[[], Session], openai_client: OpenAIClient) -> None:
        self._session_factory = session_factory
        self._openai = openai_client

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ) -> Any:
        session = self._session_factory()
        data["session"] = session
        data["openai"] = self._openai
        try:
            return await handler(event, data)
        finally:
            session.close()
