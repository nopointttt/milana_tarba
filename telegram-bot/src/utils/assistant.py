from __future__ import annotations

from typing import Dict, List
from aiogram import types

from src.utils.modes import Mode, prefix_with_mode
from src.services.openai_context_service import OpenAIContextService
from src.config import Settings
from src.db.connection import get_db_manager


async def send_with_assistant(message: types.Message, user_message: str, mode: Mode | None, context: List[Dict]) -> str:
    """Helper: отправить запрос ассистенту с учётом режима и вернуть текст ответа."""
    prefixed = prefix_with_mode(user_message, mode)
    settings = Settings.from_env()
    db_manager = get_db_manager()
    async with db_manager.get_session() as session:
        service = OpenAIContextService(api_key=settings.openai_api_key, db_session=session)
        response = await service.process_chat_mode_message(user_message=prefixed, user_id=message.from_user.id, context=context)
        return response


