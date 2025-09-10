"""src/services/memory_bank_service.py
Сервис для управления Memory Bank - персональными воспоминаниями пользователей.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlmodel import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Memory, MemoryAccess, User
from src.db.connection import DatabaseManager


logger = logging.getLogger(__name__)


class MemoryBankService:
    """Сервис для управления персональными воспоминаниями пользователей."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_memory(
        self,
        user_id: int,
        title: str,
        content: str,
        memory_type: str = "personal",
        importance: int = 5,
        tags: Optional[str] = None,
        related_memories: Optional[str] = None
    ) -> Memory:
        """Создать новое воспоминание."""
        async with self.db_manager.get_session() as session:
            memory = Memory(
                user_id=user_id,
                title=title,
                content=content,
                memory_type=memory_type,
                importance=importance,
                tags=tags,
                related_memories=related_memories
            )
            
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            
            # Логируем создание
            await self._log_access(session, memory.id, user_id, "create")
            
            logger.info(f"Создано воспоминание {memory.id} для пользователя {user_id}")
            return memory
    
    async def get_memory(self, memory_id: int, user_id: int) -> Optional[Memory]:
        """Получить воспоминание по ID."""
        async with self.db_manager.get_session() as session:
            result = await session.exec(
                select(Memory).where(
                    and_(Memory.id == memory_id, Memory.user_id == user_id)
                )
            )
            memory = result.first()
            
            if memory:
                # Обновляем время последнего доступа
                memory.last_accessed = datetime.now(timezone.utc)
                await session.commit()
                await self._log_access(session, memory_id, user_id, "read")
            
            return memory
    
    async def get_user_memories(
        self,
        user_id: int,
        memory_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Memory]:
        """Получить воспоминания пользователя с фильтрацией."""
        async with self.db_manager.get_session() as session:
            query = select(Memory).where(Memory.user_id == user_id)
            
            if memory_type:
                query = query.where(Memory.memory_type == memory_type)
            
            query = query.order_by(Memory.importance.desc(), Memory.updated_at.desc())
            query = query.offset(offset).limit(limit)
            
            result = await session.exec(query)
            memories = result.all()
            
            # Логируем доступ
            for memory in memories:
                await self._log_access(session, memory.id, user_id, "read")
            
            return memories
    
    async def search_memories(
        self,
        user_id: int,
        query_text: str,
        memory_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Memory]:
        """Поиск воспоминаний по тексту."""
        async with self.db_manager.get_session() as session:
            query = select(Memory).where(
                and_(
                    Memory.user_id == user_id,
                    or_(
                        Memory.title.ilike(f"%{query_text}%"),
                        Memory.content.ilike(f"%{query_text}%"),
                        Memory.tags.ilike(f"%{query_text}%")
                    )
                )
            )
            
            if memory_type:
                query = query.where(Memory.memory_type == memory_type)
            
            query = query.order_by(Memory.importance.desc(), Memory.updated_at.desc())
            query = query.limit(limit)
            
            result = await session.exec(query)
            memories = result.all()
            
            # Логируем доступ
            for memory in memories:
                await self._log_access(session, memory.id, user_id, "read", f"search: {query_text}")
            
            return memories
    
    async def update_memory(
        self,
        memory_id: int,
        user_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        memory_type: Optional[str] = None,
        importance: Optional[int] = None,
        tags: Optional[str] = None,
        related_memories: Optional[str] = None
    ) -> Optional[Memory]:
        """Обновить воспоминание."""
        async with self.db_manager.get_session() as session:
            result = await session.exec(
                select(Memory).where(
                    and_(Memory.id == memory_id, Memory.user_id == user_id)
                )
            )
            memory = result.first()
            
            if not memory:
                return None
            
            # Обновляем только переданные поля
            if title is not None:
                memory.title = title
            if content is not None:
                memory.content = content
            if memory_type is not None:
                memory.memory_type = memory_type
            if importance is not None:
                memory.importance = importance
            if tags is not None:
                memory.tags = tags
            if related_memories is not None:
                memory.related_memories = related_memories
            
            memory.updated_at = datetime.now(timezone.utc)
            
            await session.commit()
            await session.refresh(memory)
            
            await self._log_access(session, memory_id, user_id, "update")
            
            logger.info(f"Обновлено воспоминание {memory_id} для пользователя {user_id}")
            return memory
    
    async def delete_memory(self, memory_id: int, user_id: int) -> bool:
        """Удалить воспоминание."""
        async with self.db_manager.get_session() as session:
            result = await session.exec(
                select(Memory).where(
                    and_(Memory.id == memory_id, Memory.user_id == user_id)
                )
            )
            memory = result.first()
            
            if not memory:
                return False
            
            await session.delete(memory)
            await session.commit()
            
            await self._log_access(session, memory_id, user_id, "delete")
            
            logger.info(f"Удалено воспоминание {memory_id} для пользователя {user_id}")
            return True
    
    async def get_memory_stats(self, user_id: int) -> Dict[str, Any]:
        """Получить статистику воспоминаний пользователя."""
        async with self.db_manager.get_session() as session:
            # Общее количество воспоминаний
            total_result = await session.exec(
                select(func.count(Memory.id)).where(Memory.user_id == user_id)
            )
            total_memories = total_result.first() or 0
            
            # Количество по типам
            type_result = await session.exec(
                select(Memory.memory_type, func.count(Memory.id))
                .where(Memory.user_id == user_id)
                .group_by(Memory.memory_type)
            )
            memories_by_type = dict(type_result.all())
            
            # Последние воспоминания
            recent_result = await session.exec(
                select(Memory)
                .where(Memory.user_id == user_id)
                .order_by(Memory.updated_at.desc())
                .limit(5)
            )
            recent_memories = recent_result.all()
            
            return {
                "total_memories": total_memories,
                "memories_by_type": memories_by_type,
                "recent_memories": [
                    {
                        "id": m.id,
                        "title": m.title,
                        "type": m.memory_type,
                        "updated_at": m.updated_at.isoformat()
                    }
                    for m in recent_memories
                ]
            }
    
    async def get_related_memories(self, memory_id: int, user_id: int) -> List[Memory]:
        """Получить связанные воспоминания."""
        async with self.db_manager.get_session() as session:
            # Получаем текущее воспоминание
            result = await session.exec(
                select(Memory).where(
                    and_(Memory.id == memory_id, Memory.user_id == user_id)
                )
            )
            memory = result.first()
            
            if not memory or not memory.related_memories:
                return []
            
            # Получаем связанные воспоминания
            related_ids = [int(id_str.strip()) for id_str in memory.related_memories.split(",")]
            related_result = await session.exec(
                select(Memory).where(
                    and_(
                        Memory.id.in_(related_ids),
                        Memory.user_id == user_id
                    )
                )
            )
            
            return related_result.all()
    
    async def _log_access(
        self,
        session: AsyncSession,
        memory_id: int,
        user_id: int,
        access_type: str,
        context: Optional[str] = None
    ) -> None:
        """Логировать доступ к воспоминанию."""
        access_log = MemoryAccess(
            memory_id=memory_id,
            user_id=user_id,
            access_type=access_type,
            context=context
        )
        session.add(access_log)
        await session.commit()
    
    async def get_memory_context_for_ai(self, user_id: int, limit: int = 10) -> str:
        """Получить контекст воспоминаний для передачи в AI."""
        memories = await self.get_user_memories(user_id, limit=limit)
        
        if not memories:
            return "У пользователя пока нет сохраненных воспоминаний."
        
        context_parts = ["Контекст пользователя из Memory Bank:"]
        
        for memory in memories:
            context_parts.append(
                f"- {memory.title} ({memory.memory_type}): {memory.content}"
            )
            if memory.tags:
                context_parts.append(f"  Теги: {memory.tags}")
        
        return "\n".join(context_parts)
