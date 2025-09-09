"""src/services/user_service.py
Сервис для работы с пользователями.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User


class UserService:
    """Сервис для работы с пользователями."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create_user(
        self,
        telegram_user_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
    ) -> User:
        """Получить существующего пользователя или создать нового."""
        # Ищем существующего пользователя
        stmt = select(User).where(User.telegram_user_id == str(telegram_user_id))
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            # Обновляем данные, если они изменились
            updated = False
            if username and user.username != username:
                user.username = username
                updated = True
            if full_name and user.full_name != full_name:
                user.full_name = full_name
                updated = True
            
            if updated:
                user.updated_at = datetime.now(timezone.utc)
                self.session.add(user)
            
            return user
        
        # Создаём нового пользователя
        user = User(
            telegram_user_id=str(telegram_user_id),
            username=username,
            full_name=full_name,
        )
        self.session.add(user)
        return user
    
    async def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID."""
        stmt = select(User).where(User.telegram_user_id == str(telegram_user_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
