"""src/handlers/context_handler.py
Обработчик контекстного общения с ботом.
"""
from __future__ import annotations

import json
from typing import Dict, List, Any
from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from src.utils.modes import Mode, MARKETING_WELCOME, SALES_WELCOME, prefix_with_mode
from src.utils.assistant import send_with_assistant
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

from src.services.openai_context_service import OpenAIContextService
from src.config import Settings
from src.db.connection import get_db_manager
from src.services.analytics.chs import calc_chs
from src.services.analytics.chd import calc_chd
from src.services.analytics.name_number import calc_name_number
from src.services.analytics.matrix import build_matrix
from src.services.analytics.analytics_service import AnalyticsService
from datetime import datetime

router = Router()

# Режимы пользователя: personal | chat | marketing | sales
user_active_mode: Dict[int, str] = {}

@router.message(Command("marketing"))
async def set_mode_marketing(message: types.Message) -> None:
    user_active_mode[message.from_user.id] = Mode.marketing.value
    await message.answer(MARKETING_WELCOME)

@router.message(Command("sales"))
async def set_mode_sales(message: types.Message) -> None:
    user_active_mode[message.from_user.id] = Mode.sales.value
    await message.answer(SALES_WELCOME)

# Кнопки для ввода данных
data_input_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📝 Ввести данные", callback_data="input_data")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")]
    ]
)

# Кнопки для управления данными
data_management_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить данные", callback_data="update_data")],
        [InlineKeyboardButton(text="🗑️ Очистить дополнительные данные", callback_data="clear_additional")],
        [InlineKeyboardButton(text="🗑️ Очистить контекст", callback_data="clear_context")],
        [InlineKeyboardButton(text="ℹ️ О боте", callback_data="about")],
        [InlineKeyboardButton(text="🆘 Служба заботы", callback_data="support")]
    ]
)

# Хранилище контекста для каждого пользователя
user_contexts: Dict[int, List[Dict[str, Any]]] = {}

# Хранилище данных пользователей (имя, дата рождения)
user_data: Dict[int, Dict[str, str]] = {}

# Хранилище дополнительных данных для совместимости
additional_data: Dict[int, List[Dict[str, str]]] = {}

# Хранилище закрепленных сообщений
pinned_messages: Dict[int, int] = {}

# Флаг что данные только что обновлены
data_just_updated: Dict[int, bool] = {}

# Режим работы пользователей (True = обезличенный режим, False = персональный режим)
user_mode: Dict[int, bool] = {}

# Приветственное сообщение
WELCOME_MESSAGE = """✨ ВВЕДИТЕ ВАШИ ДАННЫЕ

Имя (только на английском):
Примеры: Olga, Maria, Ksenia 

Дата рождения:
Формат: dd.mm.yyyy
Пример: 20.05.1997

💡 СПОСОБЫ ВВОДА:

Вариант 1 - В одном сообщении:
Ivan
20.05.1997

Вариант 2 - По отдельности:
• Сначала имя
• Потом дату рождения

⚠️ ВАЖНО:
• Имя только латиницей (английскими буквами)
• Дата строго в формате dd.mm.yyyy"""


@router.message(CommandStart())
async def on_start(message: types.Message) -> None:
    """Обработчик команды /start."""
    user_id = message.from_user.id
    
    # Сбрасываем режим работы в персональный
    user_mode[user_id] = False
    
    # Очищаем контекст при новом старте
    if user_id in user_contexts:
        del user_contexts[user_id]
    
    # Инициализируем новый контекст
    user_contexts[user_id] = []
    
    # Проверяем, есть ли уже ВАЛИДНЫЕ данные пользователя
    if user_id in user_data and _has_valid_user_data(user_id):
        # Показываем закрепленное сообщение с данными
        await show_user_data_message(message)
    else:
        # Очищаем неполные данные
        if user_id in user_data:
            del user_data[user_id]
        
        # Показываем приветствие с кнопкой ввода данных
        await message.answer(
            WELCOME_MESSAGE,
            parse_mode="Markdown"
        )


@router.message(Command("menu"))
async def handle_menu_command(message: types.Message) -> None:
    """Обработчик команды /menu."""
    user_id = message.from_user.id
    
    # Показываем главное меню с командами
    menu_text = """📋 **ГЛАВНОЕ МЕНЮ**

🤖 **Доступные команды:**

🏠 `/start` - Начать работу с ботом
📋 `/menu` - Показать это меню
💬 `/chat` - Задать вопрос без даты рождения
🔄 `/update` - Ввести новую дату рождения
🗑️ `/clear` - Очистить историю
ℹ️ `/about` - О боте
🆘 `/support` - Служба заботы

💡 **Быстрые действия:**
• Просто напишите вопрос - получите ответ
• Для персонального анализа нужны ваши данные
• Используйте /chat для общих вопросов

📞 **Нужна помощь?** Используйте /support"""

    await message.answer(menu_text, parse_mode="Markdown")


@router.message(Command("chat"))
async def handle_chat_command(message: types.Message) -> None:
    """Обработчик команды /chat."""
    user_id = message.from_user.id
    
    # Переключаем в обезличенный режим
    user_mode[user_id] = True
    
    await message.answer(
        "💬 **Включен режим чата**\n\n"
        "Теперь вы можете общаться со мной без использования ваших персональных данных. "
        "Я буду отвечать на общие вопросы о цифрологии.\n\n"
        "Для возврата к персональному режиму используйте /start",
        parse_mode="Markdown"
    )


@router.message(Command("update"))
async def handle_update_command(message: types.Message) -> None:
    """Обработчик команды /update."""
    user_id = message.from_user.id
    
    # Очищаем старые данные пользователя
    if user_id in user_data:
        del user_data[user_id]
    
    # Очищаем контекст
    if user_id in user_contexts:
        del user_contexts[user_id]
    
    # Очищаем флаги
    if user_id in data_just_updated:
        del data_just_updated[user_id]
    
    # Показываем сообщение о начале обновления
    await message.answer(
        "🔄 **ОБНОВЛЕНИЕ ДАННЫХ**\n\n"
        "Сейчас введете новые данные пошагово.\n\n"
        "👤 **Шаг 1:** Введите ваше имя\n"
        "• Только английскими буквами (латиница)\n"
        "• Примеры: Ivan, Maria, John, Anna\n\n"
        "💡 **Затем** введите дату рождения:",
        parse_mode="Markdown"
    )


@router.message(Command("clear"))
async def handle_clear_command(message: types.Message) -> None:
    """Обработчик команды /clear."""
    user_id = message.from_user.id
    
    # Очищаем все данные пользователя
    if user_id in user_contexts:
        del user_contexts[user_id]
    if user_id in user_data:
        del user_data[user_id]
    if user_id in additional_data:
        del additional_data[user_id]
    if user_id in data_just_updated:
        del data_just_updated[user_id]
    if user_id in pinned_messages:
        del pinned_messages[user_id]
    
    await message.answer(
        "🗑️ **ВСЕ ДАННЫЕ ОЧИЩЕНЫ**\n\n"
        "Все ваши данные и история общения удалены.\n"
        "Используйте /start для начала работы.",
        parse_mode="Markdown"
    )


@router.message(Command("about"))
async def handle_about_command(message: types.Message) -> None:
    """Обработчик команды /about."""
    about_text = """ℹ️ **О БОТЕ**

🤖 **Цифровой Психолог по системе Миланы Тарба**

Я — ваш персональный цифровой психолог. Помогаю понять себя через анализ даты рождения и имени по системе Миланы Тарба.

🔮 **Что я умею:**
• Рассчитывать ЧС (Число Сознания)
• Вычислять ЧД (Число Действия)
• Анализировать ЧИ (Число Имени)
• Строить Матрицу Энергий
• Рассчитывать личные даты (год, месяц, день)
• Анализировать совместимость

✨ **Новые возможности:**
• Источники восстановления энергии по ЧС
• Лайфхаки общения в отношениях по ЧС
• Триггеры и раздражители по ЧС
• Карма и Дхарма: расчет и интерпретация
• Трансформация сознания: этапы и практики
• Видео‑практики из расшифровок лекций (поиск и выдача)

🎯 **Как это работает:**
1. Введите имя (английскими буквами)
2. Укажите дату рождения
3. Задавайте вопросы — получайте персональные ответы

💫 **Система Миланы Тарба** помогает раскрыть потенциал и найти гармонию.

Начните с команды /start! 🌟"""

    await message.answer(about_text, parse_mode="Markdown")


@router.message(Command("support"))
async def handle_support_command(message: types.Message) -> None:
    """Обработчик команды /support."""
    await message.answer(
        "🆘 **СЛУЖБА ЗАБОТЫ**\n\n"
        "Если у вас есть вопросы, предложения или нужна помощь, "
        "обращайтесь к нашей службе заботы!\n\n"
        "📞 **Контакты для связи:**\n"
        "• Telegram: [Написать](https://t.me/zabota_TarbaMilanabot?start=start)\n\n"
        "Мы всегда готовы помочь и ответить на ваши вопросы! 💫",
        parse_mode="Markdown"
    )




async def send_typing_status(message: types.Message) -> None:
    """Отправляет индикатор печати."""
    try:
        await message.bot.send_chat_action(message.chat.id, "typing")
    except Exception:
        pass  # Игнорируем ошибки при отправке статуса

async def send_status_message(message: types.Message, status_text: str) -> types.Message:
    """Отправляет статусное сообщение о процессе."""
    try:
        status_msg = await message.answer(f"⏳ {status_text}")
        return status_msg
    except Exception:
        return None

async def update_status_message(status_msg: types.Message, new_text: str) -> None:
    """Обновляет статусное сообщение."""
    try:
        if status_msg:
            await status_msg.edit_text(f"⏳ {new_text}")
    except Exception:
        pass  # Игнорируем ошибки при обновлении

def is_additional_data(message_text: str, user_id: int) -> bool:
    """Проверяет, является ли сообщение дополнительными данными для совместимости."""
    if user_id not in user_data:
        return False
    
    user_main_data = user_data[user_id]
    message_lower = message_text.lower()
    
    # Проверяем ключевые слова для запросов совместимости
    compatibility_keywords = [
        'совместимость', 'сравни', 'сравнение', 'партнер', 'отношения с',
        'совместим', 'подходит ли', 'подходят ли'
    ]
    
    # Проверяем, есть ли ключевые слова совместимости
    has_compatibility_keyword = any(keyword in message_lower for keyword in compatibility_keywords)
    
    if has_compatibility_keyword:
        # Ищем имя и дату в тексте
        import re
        
        # Паттерны для поиска даты
        date_patterns = [
            r'\b(\d{1,2})[.\s\-/](\d{1,2})[.\s\-/](\d{4})\b',  # 20.10.1998, 20 10 1998, 20/10/1998
            r'\b(\d{1,2})\s+(\d{1,2})\s+(\d{4})\b',  # 20 10 1998
        ]
        
        # Паттерны для поиска имени (после ключевых слов)
        name_patterns = [
            r'(?:совместимость|сравни|сравнение|партнер|отношения)\s+(?:с|со|между)\s+([а-яё]+?)(?:ом|ой|ей|ем|а|ы|и|о|у|ю)?\s+\d',  # "с давидом 20" -> "давид"
            r'с\s+([а-яё]+?)(?:ом|ой|ей|ем|а|ы|и|о|у|ю)?\s+\d',  # "с давидом 20" -> "давид"
        ]
        
        # Ищем дату
        found_date = None
        for pattern in date_patterns:
            match = re.search(pattern, message_text)
            if match:
                day, month, year = match.groups()
                found_date = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
                if is_date_format(found_date):
                    break
                else:
                    found_date = None
        
        # Ищем имя
        found_name = None
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                found_name = match.group(1).capitalize()
                break
        
        # Если нашли и имя, и дату, и они отличаются от основных данных
        if found_name and found_date:
            if (is_additional_name_format(found_name) and is_date_format(found_date) and
                (found_name != user_main_data.get('name') or 
                found_date != user_main_data.get('birth_date'))):
                return True
    
    # Поддержка многострочного ввода (2 строки) - старая логика
    lines = [line.strip() for line in message_text.strip().split('\n') if line.strip()]
    
    if len(lines) == 2:
        name, date = lines[0], lines[1]
        # Если имя или дата отличаются от основных данных пользователя
        if (is_name_format(name) and is_date_format(date) and 
            (name != user_main_data.get('name') or date != user_main_data.get('birth_date'))):
            return True
    
    # Поддержка однострочного ввода "Имя 01.01.1990"
    elif len(lines) == 1:
        text = lines[0]
        # Пытаемся разделить по пробелу
        parts = text.split()
        if len(parts) >= 2:
            # Берем последнюю часть как дату, остальное как имя
            date = parts[-1]
            name = ' '.join(parts[:-1])
            
            if (is_name_format(name) and is_date_format(date) and 
                (name != user_main_data.get('name') or date != user_main_data.get('birth_date'))):
                return True
    
    return False

def extract_additional_data(message_text: str) -> Dict[str, str]:
    """Извлекает дополнительные данные из сообщения."""
    message_lower = message_text.lower()
    
    # Проверяем ключевые слова для запросов совместимости
    compatibility_keywords = [
        'совместимость', 'сравни', 'сравнение', 'партнер', 'отношения с',
        'совместим', 'подходит ли', 'подходят ли'
    ]
    
    # Проверяем, есть ли ключевые слова совместимости
    has_compatibility_keyword = any(keyword in message_lower for keyword in compatibility_keywords)
    
    if has_compatibility_keyword:
        # Ищем имя и дату в тексте
        import re
        
        # Паттерны для поиска даты
        date_patterns = [
            r'\b(\d{1,2})[.\s\-/](\d{1,2})[.\s\-/](\d{4})\b',  # 20.10.1998, 20 10 1998, 20/10/1998
            r'\b(\d{1,2})\s+(\d{1,2})\s+(\d{4})\b',  # 20 10 1998
        ]
        
        # Паттерны для поиска имени (после ключевых слов)
        name_patterns = [
            r'(?:совместимость|сравни|сравнение|партнер|отношения)\s+(?:с|со|между)\s+([а-яё]+?)(?:ом|ой|ей|ем|а|ы|и|о|у|ю)?\s+\d',  # "с давидом 20" -> "давид"
            r'с\s+([а-яё]+?)(?:ом|ой|ей|ем|а|ы|и|о|у|ю)?\s+\d',  # "с давидом 20" -> "давид"
        ]
        
        # Ищем дату
        found_date = None
        for pattern in date_patterns:
            match = re.search(pattern, message_text)
            if match:
                day, month, year = match.groups()
                found_date = f"{day.zfill(2)}.{month.zfill(2)}.{year}"
                if is_date_format(found_date):
                    break
                else:
                    found_date = None
        
        # Ищем имя
        found_name = None
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                found_name = match.group(1).capitalize()
                break
        
        # Если нашли и имя, и дату
        if found_name and found_date and is_additional_name_format(found_name) and is_date_format(found_date):
            return {
                'name': found_name,
                'birth_date': found_date
            }
    
    # Поддержка многострочного ввода (2 строки) - старая логика
    lines = [line.strip() for line in message_text.strip().split('\n') if line.strip()]
    
    if len(lines) == 2:
        return {
            'name': lines[0],
            'birth_date': lines[1]
        }
    
    # Поддержка однострочного ввода "Имя 01.01.1990"
    elif len(lines) == 1:
        text = lines[0]
        parts = text.split()
        if len(parts) >= 2:
            # Берем последнюю часть как дату, остальное как имя
            date = parts[-1]
            name = ' '.join(parts[:-1])
            
            if is_name_format(name) and is_date_format(date):
                return {
                    'name': name,
                    'birth_date': date
                }
    
    return {}

def clear_additional_data(user_id: int) -> None:
    """Очищает дополнительные данные пользователя."""
    if user_id in additional_data:
        additional_data[user_id] = []


def _has_valid_user_data(user_id: int) -> bool:
    """Проверяет, есть ли у пользователя валидные данные (имя и дата)."""
    if user_id not in user_data:
        return False
    
    data = user_data[user_id]
    name = data.get("name", "").strip()
    birth_date = data.get("birth_date", "").strip()
    
    # Проверяем, что есть и имя, и дата, и они не дефолтные
    if not name or not birth_date:
        return False
    
    # Проверяем, что это не дефолтные значения
    if name in ["Не указано", "Хочу знать"] or birth_date == "Не указано":
        return False
    
    # Проверяем, что дата в правильном формате
    if not is_date_format(birth_date):
        return False
    
    # Проверяем, что имя в правильном формате
    if not is_name_format(name):
        return False
    
    return True

async def handle_data_input(message: types.Message) -> bool:
    """Обработка ввода данных пользователем. Возвращает True если данные обработаны."""
    user_id = message.from_user.id
    user_message = message.text.strip()
    
    # Очищаем некорректные данные ТОЛЬКО если уже введены оба поля и хотя бы одно из них невалидно
    if user_id in user_data:
        _data_chk = user_data[user_id]
        _name_chk = _data_chk.get("name", "").strip()
        _date_chk = _data_chk.get("birth_date", "").strip()
        if _name_chk and _date_chk and (not is_name_format(_name_chk) or not is_date_format(_date_chk)):
            del user_data[user_id]
    
    # Если у пользователя уже есть ВАЛИДНЫЕ данные, не обрабатываем как ввод данных
    if user_id in user_data and _has_valid_user_data(user_id):
        return False
    
    # Проверяем, является ли сообщение вводом данных
    lines = user_message.split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    if len(lines) == 2:
        # Пользователь ввел имя и дату в двух строках
        name = lines[0]
        birth_date = lines[1]
        
        # Отправляем индикатор печати
        await send_typing_status(message)
        
        # Отправляем статусное сообщение
        status_msg = await send_status_message(message, "Проверяю и сохраняю ваши данные...")
        
        # Валидируем данные
        if await validate_and_save_data(message, name, birth_date):
            # Удаляем статусное сообщение
            try:
                if status_msg:
                    await status_msg.delete()
            except Exception:
                pass
            return True
    
    elif len(lines) == 1:
        # Пользователь ввел что-то в одной строке
        text = lines[0]
        
        # Отправляем индикатор печати
        await send_typing_status(message)
        
        # Отправляем статусное сообщение
        status_msg = await send_status_message(message, "Проверяю введенные данные...")
        
        # Проверяем, является ли это комбинированным вводом "Имя Дата" или "Дата Имя"
        parts = text.split()
        if len(parts) >= 2:
            # Пробуем разные варианты парсинга
            # Вариант 1: "Имя Дата" - ищем дату в конце
            # Проверяем последние 3 части как дату (день месяц год)
            if len(parts) >= 4:
                # Пробуем последние 3 части как дату
                date_parts = parts[-3:]
                date = ' '.join(date_parts)
                name = ' '.join(parts[:-3])
                
                if is_name_format(name) and is_date_format(date):
                    # Это комбинированный ввод "Имя Дата"
                    if await validate_and_save_data(message, name, date):
                        # Удаляем статусное сообщение
                        try:
                            if status_msg:
                                await status_msg.delete()
                        except Exception:
                            pass
                        return True
            
            # Вариант 2: "Дата Имя" - ищем дату в начале
            # Проверяем первые 3 части как дату (день месяц год)
            if len(parts) >= 4:
                date_parts = parts[:3]
                date = ' '.join(date_parts)
                name = ' '.join(parts[3:])
                
                if is_date_format(date) and is_name_format(name):
                    # Это комбинированный ввод "Дата Имя"
                    if await validate_and_save_data(message, name, date):
                        # Удаляем статусное сообщение
                        try:
                            if status_msg:
                                await status_msg.delete()
                        except Exception:
                            pass
                        return True
            
            # Вариант 3: Старый способ для совместимости
            for i in range(len(parts)):
                # Вариант 3.1: "Имя Дата" - берем последнюю часть как дату
                date = parts[-1]
                name = ' '.join(parts[:-1])
                if is_name_format(name) and is_date_format(date):
                    # Это комбинированный ввод "Имя Дата"
                    if await validate_and_save_data(message, name, date):
                        # Удаляем статусное сообщение
                        try:
                            if status_msg:
                                await status_msg.delete()
                        except Exception:
                            pass
                        return True
                    break
                
                # Вариант 3.2: "Дата Имя" - берем первую часть как дату
                if i == 0:  # Проверяем только один раз
                    date = parts[0]
                    name = ' '.join(parts[1:])
                    if is_date_format(date) and is_name_format(name):
                        # Это комбинированный ввод "Дата Имя"
                        if await validate_and_save_data(message, name, date):
                            # Удаляем статусное сообщение
                            try:
                                if status_msg:
                                    await status_msg.delete()
                            except Exception:
                                pass
                            return True
                        break
        
        # Проверяем, является ли это датой
        if is_date_format(text):
            # Это дата, ждем имя
            if user_id not in user_data:
                user_data[user_id] = {}
            user_data[user_id]["birth_date"] = text
            
            # Удаляем статусное сообщение
            try:
                if status_msg:
                    await status_msg.delete()
            except Exception:
                pass
            
            # Если имя уже введено ранее — завершаем сбор данных
            if "name" in user_data[user_id] and user_data[user_id]["name"]:
                # Рассчитываем аналитику при раздельном вводе
                try:
                    _name = user_data[user_id]["name"].strip()
                    _date = user_data[user_id]["birth_date"].strip()
                    # Нормализуем дату перед расчетом
                    _date = normalize_date_format(_date)
                    user_data[user_id]["birth_date"] = _date  # Сохраняем нормализованную дату
                    print(f"🔍 DEBUG: Вызываем calculate_user_analytics из ввода даты после имени: name='{_name}', date='{_date}'")
                    user_data[user_id]["analytics"] = calculate_user_analytics(_name, _date)
                except Exception as e:
                    print(f"❌ Ошибка в вводе даты после имени: {e}")
                    import traceback
                    print(f"❌ Трейсбэк ввода даты: {traceback.format_exc()}")
                    # Устанавливаем пустую аналитику при ошибке
                    user_data[user_id]["analytics"] = {
                        'chs': None, 'chd': None, 'name_number': None,
                        'personal_year': None, 'personal_month': None, 'personal_day': None,
                        'matrix_energies': {}
                    }
                await show_user_data_message(message)
            else:
                await show_user_data_message(message) if ("name" in user_data[user_id] and user_data[user_id]["name"]) else await message.answer("✅ Дата рождения сохранена! Теперь введите ваше имя (только на английском):")
            return True
        
        # Проверяем, является ли это именем
        elif is_name_format(text):
            # Это имя, ждем дату
            if user_id not in user_data:
                user_data[user_id] = {}
            user_data[user_id]["name"] = text
            
            # Удаляем статусное сообщение
            try:
                if status_msg:
                    await status_msg.delete()
            except Exception:
                pass
            
            # Если дата уже введена ранее — завершаем сбор данных
            if "birth_date" in user_data[user_id] and user_data[user_id]["birth_date"]:
                # Рассчитываем аналитику при раздельном вводе
                try:
                    _name = user_data[user_id]["name"].strip()
                    _date = user_data[user_id]["birth_date"].strip()
                    # Нормализуем дату перед расчетом
                    _date = normalize_date_format(_date)
                    user_data[user_id]["birth_date"] = _date  # Сохраняем нормализованную дату
                    print(f"🔍 DEBUG: Вызываем calculate_user_analytics из раздельного ввода: name='{_name}', date='{_date}'")
                    user_data[user_id]["analytics"] = calculate_user_analytics(_name, _date)
                except Exception as e:
                    print(f"❌ Ошибка в раздельном вводе аналитики: {e}")
                    import traceback
                    print(f"❌ Трейсбэк раздельного ввода: {traceback.format_exc()}")
                    # Устанавливаем пустую аналитику при ошибке
                    user_data[user_id]["analytics"] = {
                        'chs': None, 'chd': None, 'name_number': None,
                        'personal_year': None, 'personal_month': None, 'personal_day': None,
                        'matrix_energies': {}
                    }
                await show_user_data_message(message)
            else:
                await message.answer("✅ Имя сохранено! Теперь введите дату рождения (dd.mm.yyyy):")
            return True
        
        # Если ничего не распознано, показываем подсказку
        else:
            # Удаляем статусное сообщение
            try:
                if status_msg:
                    await status_msg.delete()
            except Exception:
                pass
            
            await message.answer(
                "❌ Не распознал данные.\n\n" \
                "Укажите имя латиницей и дату рождения в формате dd.mm.yyyy.\n" \
                "Пример: Ivan 20.05.1997",
                parse_mode="Markdown"
            )
            return True
    
    return False


async def validate_and_save_data(message: types.Message, name: str, birth_date: str) -> bool:
    """Валидирует и сохраняет данные пользователя."""
    user_id = message.from_user.id
    
    # Валидируем имя
    if not is_name_format(name):
        await message.answer(
            "❌ **Неверный формат имени!**\n\n"
            "👤 **Требования к имени:**\n"
            "• Только английские буквы (латиница)\n"
            "• Одно слово или несколько слов\n"
            "• Примеры: Ivan, Maria, John, Anna\n\n"
            "💡 **Попробуйте еще раз:**\n"
            "```\nIvan\n20.05.1997\n```",
            parse_mode="Markdown"
        )
        return True
    
    # Валидируем дату
    if not is_date_format(birth_date):
        await message.answer(
            "❌ **Неверный формат даты!**\n\n"
            "📅 **Поддерживаемые форматы:**\n"
            "• 20.05.1997\n"
            "• 20/05/1997\n"
            "• 20-05-1997\n"
            "• 20 05 1997\n\n"
            "💡 **Попробуйте еще раз:**\n"
            "```\nIvan\n20.05.1997\n```",
            parse_mode="Markdown"
        )
        return True
    
    # Нормализуем дату
    try:
        birth_date = normalize_date_format(birth_date)
    except ValueError:
        await message.answer(
            "❌ **Ошибка при обработке даты!**\n\n"
            "📅 **Проверьте правильность даты:**\n"
            "• День: 1-31\n"
            "• Месяц: 1-12\n"
            "• Год: 1900-2100\n\n"
            "💡 **Попробуйте еще раз:**\n"
            "```\nIvan\n20.05.1997\n```",
            parse_mode="Markdown"
        )
        return True
    
    # Рассчитываем аналитику
    analytics = calculate_user_analytics(name, birth_date)
    
    # Сохраняем данные с аналитикой
    user_data[user_id] = {
        "name": name,
        "birth_date": birth_date,
        "analytics": analytics
    }
    
    # Устанавливаем флаг что данные обновлены
    data_just_updated[user_id] = True
    
    # Показываем сообщение с данными
    await show_user_data_message(message)
    
    return True


@router.message()
async def process_message(message: types.Message) -> None:
    """Обработка всех сообщений пользователя."""
    user_id = message.from_user.id
    user_message = message.text.strip()
    
    # Инициализируем контекст если его нет
    if user_id not in user_contexts:
        user_contexts[user_id] = []
    
    # Проверяем режимы
    is_chat_mode = user_mode.get(user_id, False)
    active_mode = user_active_mode.get(user_id, None)
    
    # Обезличенный режим
    if is_chat_mode:
        await handle_chat_mode_message(message)
        return
    
    # Режимы marketing/sales работают без персональных данных
    if active_mode in (Mode.marketing.value, Mode.sales.value):
        await handle_mode_message(message, Mode(active_mode))
        return
    
    # Проверяем, вводит ли пользователь данные
    if await handle_data_input(message):
        return
    
    # Проверяем, были ли данные только что обновлены
    if user_id in data_just_updated and data_just_updated[user_id]:
        print(f"🔍 DEBUG: Данные только что обновлены для пользователя {user_id}, сбрасываем флаг")
        # Сбрасываем флаг
        data_just_updated[user_id] = False
        # НЕ блокируем обработку сообщения - пользователь может сразу задать вопрос
        print(f"🔍 DEBUG: Продолжаем обработку сообщения после обновления данных")
    
    # Проверяем, есть ли у пользователя сохраненные данные
    if user_id not in user_data:
        await message.answer(
            "❌ Сначала введите ваши данные! Нажмите кнопку '📝 Ввести данные'",
            reply_markup=data_input_keyboard
        )
        return
    
    # Добавляем сообщение пользователя в контекст
    prefixed_content = prefix_with_mode(user_message, Mode(active_mode)) if active_mode else user_message
    user_contexts[user_id].append({
        "role": "user",
        "content": prefixed_content
    })
    
    try:
        # Получаем настройки
        settings = Settings.from_env()
        
        # Получаем сессию БД
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # Создаем сервис OpenAI
            openai_service = OpenAIContextService(
                api_key=settings.openai_api_key,
                db_session=session
            )
            
            # Отправляем индикатор печати
            await send_typing_status(message)
            
            # Отправляем статусное сообщение
            status_msg = await send_status_message(message, "Анализирую ваш запрос...")
            
            # Проверяем, являются ли данные дополнительными для совместимости
            if is_additional_data(user_message, user_id):
                # Обновляем статус
                await update_status_message(status_msg, "Сохраняю дополнительные данные для сравнения...")
                
                # Сохраняем дополнительные данные
                additional_info = extract_additional_data(user_message)
                
                # Рассчитываем аналитику для дополнительных данных
                additional_analytics = calculate_user_analytics(
                    additional_info['name'], 
                    additional_info['birth_date']
                )
                additional_info['analytics'] = additional_analytics
                
                if user_id not in additional_data:
                    additional_data[user_id] = []
                additional_data[user_id].append(additional_info)
                
                # Формируем сообщение с дополнительными данными
                user_data_info = user_data[user_id]
                analytics = user_data_info.get('analytics', {})
                enhanced_message = f"Пользователь: {user_message}\n\nОсновные данные пользователя:\nИмя: {user_data_info['name']}\nДата рождения: {user_data_info['birth_date']}\nЧС: {analytics.get('chs', 'N/A')}\nЧД: {analytics.get('chd', 'N/A')}\nЧИ: {analytics.get('name_number', 'N/A')}\nЛичный год: {analytics.get('personal_year', 'N/A')}\nЛичный месяц: {analytics.get('personal_month', 'N/A')}\nЛичный день: {analytics.get('personal_day', 'N/A')}\nМатрица энергий: {analytics.get('matrix_energies', {})}\n\nДополнительные данные для сравнения:\nИмя: {additional_info['name']}\nДата рождения: {additional_info['birth_date']}\nЧС: {additional_analytics.get('chs', 'N/A')}\nЧД: {additional_analytics.get('chd', 'N/A')}\nЧИ: {additional_analytics.get('name_number', 'N/A')}\nЛичный год: {additional_analytics.get('personal_year', 'N/A')}\nЛичный месяц: {additional_analytics.get('personal_month', 'N/A')}\nЛичный день: {additional_analytics.get('personal_day', 'N/A')}\nМатрица энергий: {additional_analytics.get('matrix_energies', {})}"
            else:
                # Обычное сообщение с основными данными
                user_data_info = user_data[user_id]
                analytics = user_data_info.get('analytics', {})
                enhanced_message = f"Пользователь: {user_message}\n\nДанные пользователя:\nИмя: {user_data_info['name']}\nДата рождения: {user_data_info['birth_date']}\nЧС: {analytics.get('chs', 'N/A')}\nЧД: {analytics.get('chd', 'N/A')}\nЧИ: {analytics.get('name_number', 'N/A')}\nЛичный год: {analytics.get('personal_year', 'N/A')}\nЛичный месяц: {analytics.get('personal_month', 'N/A')}\nЛичный день: {analytics.get('personal_day', 'N/A')}\nМатрица энергий: {analytics.get('matrix_energies', {})}"
            
            
            # Обновляем статус
            await update_status_message(status_msg, "Обрабатываю запрос через ИИ...")
            
            # Обрабатываем сообщение с классификацией
            print(f"🔍 DEBUG: Вызываем process_message_with_classification для сообщения: {user_message}")
            print(f"🔍 DEBUG: Пользователь {user_id}, есть ли данные: {user_id in user_data}")
            response = await openai_service.process_message_with_classification(
                user_message=enhanced_message,  # Передаем полное сообщение с данными
                user_data=analytics,  # Передаем данные пользователя
                user_id=user_id,
                context=user_contexts[user_id]
            )
            print(f"🔍 DEBUG: Получили ответ длиной {len(response)} символов")
            print(f"🔍 DEBUG: Отправляем в Telegram: {repr(response[:200])}")
            
            # Удаляем статусное сообщение
            try:
                if status_msg:
                    await status_msg.delete()
            except Exception:
                pass
            
            # Добавляем ответ бота в контекст
            user_contexts[user_id].append({
                "role": "assistant",
                "content": response
            })
            
            # Ограничиваем контекст 20 сообщениями (10 пар)
            if len(user_contexts[user_id]) > 20:
                user_contexts[user_id] = user_contexts[user_id][-20:]
            
            # Отправляем ответ с Markdown форматированием
            await message.answer(response, parse_mode="Markdown")
    
    except Exception as e:
        # Отправляем индикатор печати
        await send_typing_status(message)
        
        # Отправляем статусное сообщение об ошибке
        status_msg = await send_status_message(message, "Произошла ошибка, обрабатываю...")
        
        # Удаляем статусное сообщение
        try:
            if status_msg:
                await status_msg.delete()
        except Exception:
            pass
        
        error_message = f"❌ Извините, произошла ошибка: {str(e)}"
        await message.answer(error_message)


# Обработчики кнопок
@router.callback_query(lambda c: c.data == "input_data")
async def handle_input_data(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Ввести данные'."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    
    # Отправляем статусное сообщение
    status_msg = await send_status_message(callback_query.message, "Подготавливаю форму ввода данных...")
    
    # Удаляем предыдущее закрепленное сообщение с данными, если есть
    if user_id in pinned_messages and user_id in user_data:
        try:
            await callback_query.bot.delete_message(
                chat_id=callback_query.message.chat.id,
                message_id=pinned_messages[user_id]
            )
        except Exception as e:
            pass
        del pinned_messages[user_id]
    
    # Удаляем статусное сообщение
    try:
        if status_msg:
            await status_msg.delete()
    except Exception:
        pass
    
    # Отправляем инструкции по вводу данных
    instruction_message = """✨ ВВЕДИТЕ ВАШИ ДАННЫЕ

👤 1. Имя (только на английском):
Примеры: Ivan, Maria, John, Michael

📅 2. Дата рождения:
Формат: dd.mm.yyyy
Примеры: 20.05.1997, 01.01.1990


💡 СПОСОБЫ ВВОДА:

**Вариант 1 - В одном сообщении:**
Ivan
20.05.1997

**Вариант 2 - По отдельности:**
• Сначала имя
• Потом дату рождения

⚠️ ВАЖНО:
• Имя только латиницей (английскими буквами)
• Дата строго в формате dd.mm.yyyy
• Можно использовать пробелы в дате: 20 05 1997"""
    
    await callback_query.message.edit_text(
        instruction_message,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_input")]
            ]
        ),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data == "update_data")
async def handle_update_data(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Обновить данные'."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    
    # Отправляем статусное сообщение
    status_msg = await send_status_message(callback_query.message, "Обновляю данные...")
    
    # Очищаем ВСЕ данные пользователя
    if user_id in user_data:
        del user_data[user_id]
    clear_additional_data(user_id)
    
    # Очищаем флаг обновления данных
    if user_id in data_just_updated:
        del data_just_updated[user_id]
    
    # Очищаем закрепленное сообщение
    if user_id in pinned_messages:
        del pinned_messages[user_id]
    
    # Удаляем статусное сообщение
    try:
        if status_msg:
            await status_msg.delete()
    except Exception:
        pass
    
    # Показываем приветствие с кнопкой ввода данных
    await callback_query.message.answer(
        WELCOME_MESSAGE,
        reply_markup=data_input_keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data == "clear_additional")
async def handle_clear_additional(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Очистить дополнительные данные'."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    
    # Отправляем статусное сообщение
    status_msg = await send_status_message(callback_query.message, "Очищаю дополнительные данные...")
    
    # Очищаем дополнительные данные
    clear_additional_data(user_id)
    
    # Удаляем статусное сообщение
    try:
        if status_msg:
            await status_msg.delete()
    except Exception:
        pass
    
    # Показываем данные пользователя
    await show_user_data_message(callback_query.message)

@router.callback_query(lambda c: c.data == "cancel_input")
async def handle_cancel_input(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Отмена'."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    
    if user_id in user_data:
        # Показываем данные пользователя
        await show_user_data_message(callback_query.message)
    else:
        # Показываем приветствие
        await callback_query.message.edit_text(
            WELCOME_MESSAGE,
            reply_markup=data_input_keyboard,
            parse_mode="Markdown"
        )


@router.callback_query(lambda c: c.data == "about")
async def handle_about_callback(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'О боте'."""
    await callback_query.answer()
    
    about_text = """ℹ️ **О БОТЕ**

🤖 **Цифровой Психолог по системе Миланы Тарба**

Я — ваш персональный цифровой психолог. Помогаю понять себя через анализ даты рождения и имени по системе Миланы Тарба.

🔮 **Что я умею:**
• Рассчитывать ЧС (Число Сознания)
• Вычислять ЧД (Число Действия)
• Анализировать ЧИ (Число Имени)
• Строить Матрицу Энергий
• Рассчитывать личные даты (год, месяц, день)
• Анализировать совместимость

✨ **Новые возможности:**
• Источники восстановления энергии по ЧС
• Лайфхаки общения в отношениях по ЧС
• Триггеры и раздражители по ЧС
• Карма и Дхарма: расчет и интерпретация
• Трансформация сознания: этапы и практики
• Видео‑практики из расшифровок лекций (поиск и выдача)

🎯 **Как это работает:**
1. Введите имя (английскими буквами)
2. Укажите дату рождения
3. Задавайте вопросы — получайте персональные ответы

💫 **Система Миланы Тарба** помогает раскрыть потенциал и найти гармонию.

Начните с команды /start! 🌟"""
    
    await callback_query.message.edit_text(
        about_text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ]
        ),
        parse_mode="Markdown"
    )


@router.callback_query(lambda c: c.data == "back_to_main")
async def handle_back_to_main(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Назад'."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    
    if user_id in user_data:
        # Показываем данные пользователя
        await show_user_data_message(callback_query.message)
    else:
        # Показываем приветствие
        await callback_query.message.edit_text(
            WELCOME_MESSAGE,
            reply_markup=data_input_keyboard,
            parse_mode="Markdown"
        )


@router.callback_query(lambda c: c.data == "chat_mode")
async def handle_chat_mode(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Чат' - переключение в обезличенный режим."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    
    # Переключаем в обезличенный режим
    user_mode[user_id] = True
    
    # Очищаем контекст для нового режима
    if user_id in user_contexts:
        del user_contexts[user_id]
    
    chat_mode_message = """💬 ОБЕЗЛИЧЕННЫЙ РЕЖИМ АКТИВИРОВАН

Теперь я работаю как обычный чат с GPT, но с базой знаний по цифрологии Миланы Тарба.

✨ Что изменилось:
• Не требую ваши персональные данные
• Не делаю персональные разборы
• Отвечаю на общие вопросы о цифрологии
• Помогаю с теорией и практиками

💡 Примеры вопросов:
• "Что такое Число Сознания?"
• "Как рассчитать матрицу?"
• "Какие практики для энергии 7?"
• "Расскажи про совместимость в цифрологии"

🔙 Для возврата в персональный режим нажмите /start"""
    
    await callback_query.message.edit_text(
        chat_mode_message,
        # parse_mode="Markdown"  # Убрано для избежания ошибок парсинга
    )


@router.callback_query(lambda c: c.data == "clear_context")
async def handle_clear_context_callback(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Очистить контекст'."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    
    # Очищаем контекст беседы
    if user_id in user_contexts:
        del user_contexts[user_id]
    
    # Очищаем личные данные пользователя
    if user_id in user_data:
        del user_data[user_id]
    
    # Очищаем дополнительные данные
    clear_additional_data(user_id)
    
    # Очищаем флаг обновления данных
    if user_id in data_just_updated:
        del data_just_updated[user_id]
    
    # Очищаем закрепленное сообщение
    if user_id in pinned_messages:
        del pinned_messages[user_id]
    
    # Сбрасываем режим
    user_mode[user_id] = False
    
    clear_message = """🗑️ ВСЕ ДАННЫЕ ОЧИЩЕНЫ

История диалога и личные данные очищены. Бот "забыл" все предыдущие сообщения и ваши данные.

Теперь можете начать с чистого листа! 💫

Нажмите /start для ввода новых данных."""
    
    await callback_query.message.edit_text(
        clear_message,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ]
        )
    )


@router.callback_query(lambda c: c.data == "support")
async def handle_support_callback(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Служба заботы'."""
    await callback_query.answer()
    
    support_message = """🆘 **СЛУЖБА ЗАБОТЫ**

Если у вас есть вопросы, предложения или нужна помощь, 
обращайтесь к нашей службе заботы!

📞 **Контакты для связи:**
• Telegram: [Написать](https://t.me/zabota_TarbaMilanabot?start=start)

Мы всегда готовы помочь и ответить на ваши вопросы! 💫"""
    
    await callback_query.message.edit_text(
        support_message,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
            ]
        ),
        parse_mode="Markdown"
    )


async def handle_chat_mode_message(message: types.Message) -> None:
    """Обработка сообщений в обезличенном режиме."""
    user_id = message.from_user.id
    user_message = message.text.strip()
    
    # Добавляем сообщение пользователя в контекст
    user_contexts[user_id].append({
        "role": "user",
        "content": user_message
    })
    
    try:
        # Получаем настройки
        settings = Settings.from_env()
        
        # Получаем сессию БД
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            # Создаем сервис OpenAI для обезличенного режима
            openai_service = OpenAIContextService(
                api_key=settings.openai_api_key,
                db_session=session
            )
            
            # Отправляем индикатор печати
            await send_typing_status(message)
            
            # Отправляем статусное сообщение
            status_msg = await send_status_message(message, "Обрабатываю ваш запрос...")
            
            # Обрабатываем сообщение в обезличенном режиме
            response = await openai_service.process_chat_mode_message(
                user_message=user_message,
                user_id=user_id,
                context=user_contexts[user_id]
            )
            
            # Удаляем статусное сообщение
            try:
                if status_msg:
                    await status_msg.delete()
            except Exception:
                pass
            
            # Добавляем ответ бота в контекст
            user_contexts[user_id].append({
                "role": "assistant",
                "content": response
            })
            
            # Ограничиваем контекст 20 сообщениями (10 пар)
            if len(user_contexts[user_id]) > 20:
                user_contexts[user_id] = user_contexts[user_id][-20:]
            
            # Отправляем ответ с Markdown форматированием
            await message.answer(response, parse_mode="Markdown")
    
    except Exception as e:
        # Отправляем индикатор печати
        await send_typing_status(message)
        
        # Отправляем статусное сообщение об ошибке
        status_msg = await send_status_message(message, "Произошла ошибка, обрабатываю...")
        
        # Удаляем статусное сообщение
        try:
            if status_msg:
                await status_msg.delete()
        except Exception:
            pass
        
        error_message = f"❌ Извините, произошла ошибка: {str(e)}"
        await message.answer(error_message)


async def show_user_data_message(message: types.Message) -> None:
    """Показать сообщение с данными пользователя."""
    user_id = message.from_user.id
    
    if user_id not in user_data:
        return
    
    # Проверяем, что данные валидные
    if not _has_valid_user_data(user_id):
        return
    
    data = user_data[user_id]
    name = data.get("name", "Не указано")
    birth_date = data.get("birth_date", "Не указано")
    analytics = data.get("analytics", {})
    
    # Проверяем наличие дополнительных данных
    additional_count = len(additional_data.get(user_id, []))
    
    data_message = f"""✨ ДАННЫЕ СОХРАНЕНЫ!

👤 Имя: {name}
📅 Дата рождения: {birth_date}

• ЧС (Число Сознания): {analytics.get('chs', 'N/A')}
• ЧД (Число Действия): {analytics.get('chd', 'N/A')}
• ЧИ (Число Имени): {analytics.get('name_number', 'N/A')}

• Личный год: {analytics.get('personal_year', 'N/A')}
• Личный месяц: {analytics.get('personal_month', 'N/A')}
• Личный день: {analytics.get('personal_day', 'N/A')}

МАТРИЦА ЭНЕРГИЙ:"""
    
    # Добавляем матрицу энергий в требуемом формате (только описания без количеств)
    matrix_descriptions = {
        1: "Принятие решений / психическая энергия / ответственность",
        2: "Дипломатия / понимание / чувственность, детальность / исполнительность",
        3: "Творчество / самовыражение / общительность",
        4: "Стабильность / система / дисциплина",
        5: "Свобода / движение / гибкость",
        6: "Забота / гармония / ответственность за близких",
        7: "Мудрость / внутренняя опора / интуиция",
        8: "Труд / упорство / способность учиться на своих ошибках / чувство долга / ответственность",
        9: "Завершение / гуманизм / масштаб мышления",
    }
    digit_counts = analytics.get('matrix_digit_counts', {}) or {}
    for digit in range(1, 10):
        count = digit_counts.get(digit, 0)
        if count and digit in matrix_descriptions:
            data_message += f"\n• Энергия {digit}: {matrix_descriptions[digit]}"
    
    if additional_count > 0:
        data_message += f"\n\n📊 Дополнительные данные для сравнения: {additional_count} человек"
    
    data_message += f"""


💬 Теперь просто пишите запросы:
• Дай мне прогноз на год
• Расскажи про мою матрицу  
• Нужны практики для уверенности
• Помоги с отношениями
• Сравни меня с [Имя] [Дата] - для совместимости

🤖 Команды бота (в меню):
/menu - Показать главное меню
/chat - Обезличенный режим
/update - Обновить данные
/clear - Очистить контекст
/about - О боте
/support - Служба заботы

Я буду использовать ваши сохраненные данные для всех анализов! 💫"""
    
    sent_message = await message.answer(
        data_message,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    
    # Сохраняем ID закрепленного сообщения
    pinned_messages[user_id] = sent_message.message_id


def get_user_context(user_id: int) -> List[Dict[str, Any]]:
    """Получить контекст пользователя."""
    return user_contexts.get(user_id, [])


def clear_user_context(user_id: int) -> None:
    """Очистить контекст пользователя."""
    if user_id in user_contexts:
        del user_contexts[user_id]


def is_name_format(name: str) -> bool:
    """Проверяет, что имя написано на английском языке (латиницей)."""
    if not name or not name.strip():
        return False
    
    # Убираем пробелы
    name = name.strip()
    
    # Проверяем, что все символы - латинские буквы
    return name.replace(' ', '').isalpha() and all(ord(c) < 128 for c in name)

def is_additional_name_format(name: str) -> bool:
    """Проверяет, что имя подходит для дополнительных данных (может быть на любом языке)."""
    if not name or not name.strip():
        return False
    
    # Убираем пробелы
    name = name.strip()
    
    # Проверяем, что все символы - буквы (любого алфавита)
    return name.replace(' ', '').isalpha()


def normalize_date_format(date_str: str) -> str:
    """Нормализует дату в стандартный формат dd.mm.yyyy."""
    if not date_str or not date_str.strip():
        raise ValueError("Дата не может быть пустой")
    
    date_str = date_str.strip()
    
    # Сначала пробуем стандартные форматы
    from datetime import datetime
    import re
    
    date_formats = ["%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d %m %Y"]
    
    for fmt in date_formats:
        try:
            d = datetime.strptime(date_str, fmt)
            return d.strftime("%d.%m.%Y")
        except ValueError:
            continue
    
    # Если стандартные форматы не сработали, пробуем формат с пробелами
    if re.match(r'^\d{1,2}\s+\d{1,2}\s+\d{4}$', date_str):
        # Заменяем пробелы на точки
        normalized_date = re.sub(r'\s+', '.', date_str)
        try:
            d = datetime.strptime(normalized_date, "%d.%m.%Y")
            return d.strftime("%d.%m.%Y")
        except ValueError:
            pass
    
    raise ValueError(f"Неподдерживаемый формат даты: {date_str}")


def is_date_format(date_str: str) -> bool:
    """Проверяет формат даты."""
    try:
        normalize_date_format(date_str)
        return True
    except ValueError:
        return False


def calculate_user_analytics(name: str, birth_date: str) -> dict:
    """Рассчитывает аналитику пользователя программно."""
    try:
        print(f"🔍 DEBUG calculate_user_analytics: name='{name}', birth_date='{birth_date}'")
        
        # Создаем сервис аналитики
        analytics_service = AnalyticsService()
        print(f"🔍 DEBUG: AnalyticsService создан успешно")
        
        # Выполняем полный анализ
        print(f"🔍 DEBUG: Вызываем analyze_person...")
        result = analytics_service.analyze_person(birth_date, name)
        print(f"🔍 DEBUG: Результат analyze_person получен: {type(result)}")
        print(f"🔍 DEBUG: Ключи результата: {list(result.keys())}")
        
        # Извлекаем данные из правильной структуры
        calculations = result.get('calculations', {})
        matrix_data = result.get('matrix', {})
        
        # Создаем матрицу энергий с описаниями
        matrix_energies = {}
        energy_descriptions = {
            "1": "Лидерство",
            "2": "Дипломатия", 
            "3": "Творчество",
            "4": "Стабильность",
            "5": "Свобода",
            "6": "Гармония",
            "7": "Мудрость",
            "8": "Материя",
            "9": "Завершение"
        }
        
        digit_counts = matrix_data.get('digit_counts', {})
        for i in range(1, 10):
            count = digit_counts.get(i, 0)
            if count > 0:
                description = energy_descriptions.get(str(i), "")
                matrix_energies[str(i)] = f"{count} ({description})"
        
        # Возвращаем данные в нужном формате
        return {
            'chs': calculations.get('consciousness_number'),
            'chd': calculations.get('action_number'),
            'name_number': calculations.get('name_number'),
            'personal_year': calculations.get('personal_year'),
            'personal_month': calculations.get('personal_month'),
            'personal_day': calculations.get('personal_day'),
            'matrix_energies': matrix_energies,
            'matrix_digit_counts': digit_counts,
            'matrix_strong_digits': matrix_data.get('strong_digits', []),
            'matrix_weak_digits': matrix_data.get('weak_digits', []),
            'matrix_missing_digits': matrix_data.get('missing_digits', [])
        }
    except Exception as e:
        print(f"❌ Ошибка расчета аналитики: {e}")
        print(f"❌ Тип ошибки: {type(e).__name__}")
        import traceback
        print(f"❌ Трейсбэк: {traceback.format_exc()}")
        return {
            'chs': None,
            'chd': None,
            'name_number': None,
            'personal_year': None,
            'personal_month': None,
            'personal_day': None,
            'matrix_energies': {},
            'matrix_digit_counts': {},
            'matrix_strong_digits': [],
            'matrix_weak_digits': [],
            'matrix_missing_digits': []
        }

async def handle_mode_message(message: types.Message, mode: Mode) -> None:
    """Обработка сообщений в режимах marketing/sales без персональных данных."""
    user_id = message.from_user.id
    user_message = message.text.strip()
    
    # Добавляем в контекст с маркером режима
    mode_prefixed = prefix_with_mode(user_message, mode)
    user_contexts[user_id].append({
        "role": "user",
        "content": mode_prefixed
    })
    
    try:
        settings = Settings.from_env()
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            openai_service = OpenAIContextService(
                api_key=settings.openai_api_key,
                db_session=session
            )
            await send_typing_status(message)
            status_msg = await send_status_message(message, "Обрабатываю ваш запрос...")
            response = await send_with_assistant(message, user_message, mode, user_contexts[user_id])
            try:
                if status_msg:
                    await status_msg.delete()
            except Exception:
                pass
            await message.answer(response)
    except Exception as e:
        await message.answer(f"❌ Извините, произошла ошибка при обработке запроса: {str(e)}")