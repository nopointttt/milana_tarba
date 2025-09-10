"""src/handlers/memory_handler.py
Обработчики команд для работы с Memory Bank.
"""
from __future__ import annotations

import logging
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.services.memory_bank_service import MemoryBankService
from src.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

router = Router()


class MemoryStates(StatesGroup):
    """Состояния для работы с воспоминаниями."""
    waiting_for_title = State()
    waiting_for_content = State()
    waiting_for_type = State()
    waiting_for_importance = State()
    waiting_for_tags = State()
    editing_memory = State()
    searching_memories = State()


@router.message(Command("memory"))
async def memory_menu(message: Message, state: FSMContext):
    """Главное меню Memory Bank."""
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Создать воспоминание", callback_data="memory_create")],
        [InlineKeyboardButton(text="🔍 Поиск воспоминаний", callback_data="memory_search")],
        [InlineKeyboardButton(text="📋 Мои воспоминания", callback_data="memory_list")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="memory_stats")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="memory_cancel")]
    ])
    
    await message.answer(
        "🧠 **Memory Bank** - Ваше персональное хранилище воспоминаний\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "memory_create")
async def start_create_memory(callback: CallbackQuery, state: FSMContext):
    """Начать создание воспоминания."""
    await callback.answer()
    await state.set_state(MemoryStates.waiting_for_title)
    
    await callback.message.edit_text(
        "📝 **Создание воспоминания**\n\n"
        "Введите название воспоминания:",
        parse_mode="Markdown"
    )


@router.message(MemoryStates.waiting_for_title)
async def process_title(message: Message, state: FSMContext):
    """Обработать название воспоминания."""
    title = message.text.strip()
    if len(title) > 100:
        await message.answer("❌ Название слишком длинное. Максимум 100 символов.")
        return
    
    await state.update_data(title=title)
    await state.set_state(MemoryStates.waiting_for_content)
    
    await message.answer(
        f"✅ Название: **{title}**\n\n"
        "Теперь введите содержимое воспоминания:",
        parse_mode="Markdown"
    )


@router.message(MemoryStates.waiting_for_content)
async def process_content(message: Message, state: FSMContext):
    """Обработать содержимое воспоминания."""
    content = message.text.strip()
    if len(content) > 2000:
        await message.answer("❌ Содержимое слишком длинное. Максимум 2000 символов.")
        return
    
    await state.update_data(content=content)
    await state.set_state(MemoryStates.waiting_for_type)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Личное", callback_data="type_personal")],
        [InlineKeyboardButton(text="⭐ Предпочтения", callback_data="type_preference")],
        [InlineKeyboardButton(text="🎯 Цели", callback_data="type_goal")],
        [InlineKeyboardButton(text="💡 Идеи", callback_data="type_idea")],
        [InlineKeyboardButton(text="📚 Знания", callback_data="type_knowledge")],
        [InlineKeyboardButton(text="🔗 Контекст", callback_data="type_context")]
    ])
    
    await message.answer(
        f"✅ Содержимое сохранено\n\n"
        "Выберите тип воспоминания:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("type_"))
async def process_type(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор типа воспоминания."""
    await callback.answer()
    
    type_mapping = {
        "type_personal": "personal",
        "type_preference": "preference", 
        "type_goal": "goal",
        "type_idea": "idea",
        "type_knowledge": "knowledge",
        "type_context": "context"
    }
    
    memory_type = type_mapping[callback.data]
    await state.update_data(memory_type=memory_type)
    await state.set_state(MemoryStates.waiting_for_importance)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1", callback_data="imp_1"),
         InlineKeyboardButton(text="2", callback_data="imp_2"),
         InlineKeyboardButton(text="3", callback_data="imp_3")],
        [InlineKeyboardButton(text="4", callback_data="imp_4"),
         InlineKeyboardButton(text="5", callback_data="imp_5"),
         InlineKeyboardButton(text="6", callback_data="imp_6")],
        [InlineKeyboardButton(text="7", callback_data="imp_7"),
         InlineKeyboardButton(text="8", callback_data="imp_8"),
         InlineKeyboardButton(text="9", callback_data="imp_9")],
        [InlineKeyboardButton(text="10", callback_data="imp_10")]
    ])
    
    await callback.message.edit_text(
        f"✅ Тип: **{memory_type}**\n\n"
        "Выберите важность (1-10):",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("imp_"))
async def process_importance(callback: CallbackQuery, state: FSMContext):
    """Обработать выбор важности."""
    await callback.answer()
    
    importance = int(callback.data.split("_")[1])
    await state.update_data(importance=importance)
    await state.set_state(MemoryStates.waiting_for_tags)
    
    await callback.message.edit_text(
        f"✅ Важность: **{importance}/10**\n\n"
        "Введите теги через запятую (необязательно):\n"
        "Например: работа, важное, проект",
        parse_mode="Markdown"
    )


@router.message(MemoryStates.waiting_for_tags)
async def process_tags(message: Message, state: FSMContext):
    """Обработать теги и создать воспоминание."""
    tags = message.text.strip() if message.text else None
    
    # Получаем данные из состояния
    data = await state.get_data()
    
    # Создаем воспоминание
    db_manager = DatabaseManager()
    memory_service = MemoryBankService(db_manager)
    
    try:
        memory = await memory_service.create_memory(
            user_id=message.from_user.id,
            title=data["title"],
            content=data["content"],
            memory_type=data["memory_type"],
            importance=data["importance"],
            tags=tags
        )
        
        await state.clear()
        
        await message.answer(
            f"✅ **Воспоминание создано!**\n\n"
            f"📝 **{memory.title}**\n"
            f"📂 Тип: {memory.memory_type}\n"
            f"⭐ Важность: {memory.importance}/10\n"
            f"🏷️ Теги: {memory.tags or 'не указаны'}\n"
            f"🆔 ID: {memory.id}",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка создания воспоминания: {e}")
        await message.answer("❌ Ошибка при создании воспоминания. Попробуйте позже.")


@router.callback_query(F.data == "memory_search")
async def start_search(callback: CallbackQuery, state: FSMContext):
    """Начать поиск воспоминаний."""
    await callback.answer()
    await state.set_state(MemoryStates.searching_memories)
    
    await callback.message.edit_text(
        "🔍 **Поиск воспоминаний**\n\n"
        "Введите поисковый запрос:",
        parse_mode="Markdown"
    )


@router.message(MemoryStates.searching_memories)
async def process_search(message: Message, state: FSMContext):
    """Обработать поисковый запрос."""
    query = message.text.strip()
    
    db_manager = DatabaseManager()
    memory_service = MemoryBankService(db_manager)
    
    try:
        memories = await memory_service.search_memories(
            user_id=message.from_user.id,
            query_text=query,
            limit=10
        )
        
        if not memories:
            await message.answer("❌ Воспоминания не найдены.")
            return
        
        result_text = f"🔍 **Результаты поиска по запросу: {query}**\n\n"
        
        for i, memory in enumerate(memories, 1):
            result_text += (
                f"{i}. **{memory.title}**\n"
                f"   📂 {memory.memory_type} | ⭐ {memory.importance}/10\n"
                f"   📝 {memory.content[:100]}{'...' if len(memory.content) > 100 else ''}\n"
                f"   🆔 ID: {memory.id}\n\n"
            )
        
        await message.answer(result_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка поиска воспоминаний: {e}")
        await message.answer("❌ Ошибка при поиске воспоминаний.")


@router.callback_query(F.data == "memory_list")
async def list_memories(callback: CallbackQuery):
    """Показать список воспоминаний."""
    await callback.answer()
    
    db_manager = DatabaseManager()
    memory_service = MemoryBankService(db_manager)
    
    try:
        memories = await memory_service.get_user_memories(
            user_id=callback.from_user.id,
            limit=10
        )
        
        if not memories:
            await callback.message.edit_text("❌ У вас пока нет воспоминаний.")
            return
        
        result_text = "📋 **Ваши воспоминания**\n\n"
        
        for i, memory in enumerate(memories, 1):
            result_text += (
                f"{i}. **{memory.title}**\n"
                f"   📂 {memory.memory_type} | ⭐ {memory.importance}/10\n"
                f"   📝 {memory.content[:100]}{'...' if len(memory.content) > 100 else ''}\n"
                f"   🆔 ID: {memory.id}\n\n"
            )
        
        await callback.message.edit_text(result_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка получения списка воспоминаний: {e}")
        await callback.message.edit_text("❌ Ошибка при получении списка воспоминаний.")


@router.callback_query(F.data == "memory_stats")
async def show_stats(callback: CallbackQuery):
    """Показать статистику воспоминаний."""
    await callback.answer()
    
    db_manager = DatabaseManager()
    memory_service = MemoryBankService(db_manager)
    
    try:
        stats = await memory_service.get_memory_stats(user_id=callback.from_user.id)
        
        result_text = "📊 **Статистика Memory Bank**\n\n"
        result_text += f"📝 Всего воспоминаний: **{stats['total_memories']}**\n\n"
        
        if stats['memories_by_type']:
            result_text += "📂 По типам:\n"
            for mem_type, count in stats['memories_by_type'].items():
                result_text += f"   • {mem_type}: {count}\n"
        
        if stats['recent_memories']:
            result_text += "\n🕒 Последние воспоминания:\n"
            for memory in stats['recent_memories']:
                result_text += f"   • {memory['title']} ({memory['type']})\n"
        
        await callback.message.edit_text(result_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        await callback.message.edit_text("❌ Ошибка при получении статистики.")


@router.callback_query(F.data == "memory_cancel")
async def cancel_memory_operation(callback: CallbackQuery, state: FSMContext):
    """Отменить операцию с воспоминаниями."""
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("❌ Операция отменена.")


# Команды для быстрого доступа
@router.message(Command("memories"))
async def quick_memories_list(message: Message):
    """Быстрый список воспоминаний."""
    await list_memories(message)


@router.message(Command("memsearch"))
async def quick_memory_search(message: Message, state: FSMContext):
    """Быстрый поиск воспоминаний."""
    await start_search(message, state)
