"""src/handlers/step_handler.py
Обработчик пошагового ввода данных для анализов.
"""
from __future__ import annotations

import asyncio
from typing import Dict, Any, Optional
from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.services.analytics.analytics_service import AnalyticsService
from src.services.user_service import UserService
from src.services.analytics_storage import AnalyticsStorageService
from src.services.openai_service import OpenAIService
from src.db.connection import get_db_manager
from src.config import Settings

router = Router()
analytics_service = AnalyticsService()

# Хранилище для данных пользователей
user_data: Dict[int, Dict[str, Any]] = {}


def format_openai_response(text: str) -> str:
    """Форматирует ответ от OpenAI для красивого отображения в Telegram."""
    import re
    
    # Убираем лишние пробелы и переносы
    text = text.strip()
    
    # Удаляем HTML теги (на всякий случай, если OpenAI их вернет)
    text = re.sub(r'<[^>]+>', '', text)
    
    # Убираем HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    
    # Убираем проблемные Markdown символы, которые могут вызвать ошибки парсинга
    text = re.sub(r'```[^`]*```', '', text)  # Убираем блоки кода
    text = re.sub(r'`[^`]*`', '', text)      # Убираем inline код
    text = re.sub(r'#{1,6}\s+', '', text)    # Убираем заголовки
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)  # Убираем списки
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)  # Убираем нумерованные списки
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)  # Убираем ссылки, оставляем текст
    
    # Исправляем некорректные Markdown символы
    text = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', text)  # Исправляем жирный текст
    text = re.sub(r'\*([^*]+)\*', r'*\1*', text)        # Исправляем курсив
    
    # Убираем одиночные звездочки и подчеркивания, которые могут сломать парсинг
    text = re.sub(r'(?<!\*)\*(?!\*)', '', text)  # Убираем одиночные *
    text = re.sub(r'(?<!_)_(?!_)', '', text)     # Убираем одиночные _
    text = re.sub(r'(?<!`)`(?!`)', '', text)     # Убираем одиночные `
    
    # Добавляем эмоджи к заголовкам
    text = text.replace("✨ Твой персональный профиль", "✨ **Твой персональный профиль**")
    text = text.replace("❤️ Глубокий анализ чисел", "❤️ **Глубокий анализ чисел**")
    text = text.replace("💎 Матрица твоих энергий", "💎 **Матрица твоих энергий**")
    text = text.replace("💡 Твои точки роста и практики", "💡 **Твои точки роста и практики**")
    
    # Добавляем жирный текст к подзаголовкам
    text = text.replace("➡️ Практика", "➡️ **Практика**")
    text = text.replace("➡️ Если появится желание", "➡️ **Если появится желание**")
    
    # Добавляем курсив к важным фразам
    text = text.replace("Дорогая", "*Дорогая")
    text = text.replace("С теплом и заботой,", "*С теплом и заботой,*")
    text = text.replace("Милана", "Милана*")
    
    # Финальная очистка - убираем множественные пробелы и переносы
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Максимум 2 переноса подряд
    text = re.sub(r' +', ' ', text)               # Убираем множественные пробелы
    
    return text

async def send_long_message(message: types.Message, text: str, max_length: int = 4000) -> None:
    """Отправляет длинное сообщение частями с красивым форматированием."""
    import re
    
    # Форматируем текст
    formatted_text = format_openai_response(text)
    
    if len(formatted_text) <= max_length:
        try:
            await message.answer(formatted_text, parse_mode="Markdown")
            return
        except Exception as e:
            print(f"⚠️ Markdown parsing error, sending as plain text: {e}")
            # Fallback: отправляем как обычный текст без форматирования
            plain_text = re.sub(r'[*_`]', '', formatted_text)  # Убираем все Markdown символы
            await message.answer(plain_text)
            return
    
    # Разбиваем по разделам
    sections = formatted_text.split('\n\n')
    current_message = ""
    
    for section in sections:
        # Если добавление раздела превысит лимит
        if len(current_message) + len(section) + 2 > max_length:
            # Отправляем текущее сообщение
            if current_message.strip():
                try:
                    await message.answer(current_message.strip(), parse_mode="Markdown")
                except Exception as e:
                    print(f"⚠️ Markdown parsing error, sending as plain text: {e}")
                    # Fallback: отправляем как обычный текст
                    plain_text = re.sub(r'[*_`]', '', current_message.strip())
                    await message.answer(plain_text)
                await asyncio.sleep(0.5)  # Небольшая пауза между сообщениями
            
            # Начинаем новое сообщение с текущего раздела
            current_message = section
        else:
            # Добавляем раздел к текущему сообщению
            if current_message:
                current_message += "\n\n" + section
            else:
                current_message = section
    
    # Отправляем последнее сообщение
    if current_message.strip():
        try:
            await message.answer(current_message.strip(), parse_mode="Markdown")
        except Exception as e:
            print(f"⚠️ Markdown parsing error, sending as plain text: {e}")
            # Fallback: отправляем как обычный текст
            plain_text = re.sub(r'[*_`]', '', current_message.strip())
            await message.answer(plain_text)


@router.message()
async def process_user_input(message: types.Message) -> None:
    """Обработка ввода пользователя."""
    text = message.text.strip()
    user_id = message.from_user.id
    
    # Проверяем, есть ли у пользователя сохранённые данные
    if user_id not in user_data:
        user_data[user_id] = {}
    
    current_state = user_data[user_id].get('state', '')
    
    # Обработка разных состояний
    if current_state == 'full_analysis_query':
        await handle_full_analysis_query(message, text)
    elif current_state == 'full_analysis_date':
        await handle_full_analysis_date(message, text)
    elif current_state == 'full_analysis_name':
        await handle_full_analysis_name(message, text)
    elif current_state == 'consciousness_query':
        await handle_consciousness_query(message, text)
    elif current_state == 'consciousness_date':
        await handle_consciousness_date(message, text)
    elif current_state == 'action_query':
        await handle_action_query(message, text)
    elif current_state == 'action_date':
        await handle_action_date(message, text)
    elif current_state == 'name_query':
        await handle_name_query(message, text)
    elif current_state == 'name_input':
        await handle_name_input(message, text)
    elif current_state == 'matrix_query':
        await handle_matrix_query(message, text)
    elif current_state == 'matrix_date':
        await handle_matrix_date(message, text)
    elif current_state == 'practices_query':
        await handle_practices_query(message, text)
    else:
        # Если не в процессе анализа, показываем помощь
        await message.answer(
            "❓ **Не понимаю команду.**\n\n"
            "Используйте меню ниже для выбора нужного анализа 👇",
            parse_mode="Markdown"
        )


# === ПОЛНЫЙ АНАЛИЗ ===

async def handle_full_analysis_query(message: types.Message, query: str) -> None:
    """Обработка запроса для полного анализа."""
    user_id = message.from_user.id
    user_data[user_id]['query'] = query
    user_data[user_id]['state'] = 'full_analysis_date'
    
    await message.answer(
        "**📅 Шаг 2 из 3: Дата рождения**\n\n"
        "Введите дату рождения в формате dd.mm.yyyy\n\n"
"Например: 20.05.1997",
        parse_mode="Markdown"
    )


async def handle_full_analysis_date(message: types.Message, date_str: str) -> None:
    """Обработка даты для полного анализа."""
    if not analytics_service.validate_birth_date(date_str):
        await message.answer(
            "❌ **Неверный формат даты.**\n\n"
            "Введите дату в формате dd.mm.yyyy\n"
"Например: 20.05.1997",
            parse_mode="Markdown"
        )
        return
    
    user_id = message.from_user.id
    user_data[user_id]['birth_date'] = date_str
    user_data[user_id]['state'] = 'full_analysis_name'
    
    await message.answer(
        "**👤 Шаг 3 из 3: Имя**\n\n"
        "Введите ваше полное имя (кириллица или латиница)\n\n"
        "*Например: `Иван Петров` или `Ivan Petrov`*",
        parse_mode="Markdown"
    )


async def handle_full_analysis_name(message: types.Message, name: str) -> None:
    """Обработка имени для полного анализа."""
    if not analytics_service.validate_name(name):
        await message.answer(
            "❌ **Неверный формат имени.**\n\n"
            "Введите ваше полное имя (только буквы)\n"
            "Например: `Иван Петров`",
            parse_mode="Markdown"
        )
        return
    
    user_id = message.from_user.id
    user_data[user_id]['name'] = name
    
    # Выполняем полный анализ
    await perform_full_analysis(message, user_data[user_id])
    
    # Очищаем данные
    del user_data[user_id]


# === ЧИСЛО СОЗНАНИЯ ===

async def handle_consciousness_query(message: types.Message, query: str) -> None:
    """Обработка запроса для анализа числа сознания."""
    user_id = message.from_user.id
    user_data[user_id]['query'] = query
    user_data[user_id]['state'] = 'consciousness_date'
    
    await message.answer(
        "**📅 Шаг 2 из 2: Дата рождения**\n\n"
        "Введите дату рождения в формате `dd.mm.yyyy`\n\n"
        "*Например: `20.05.1997`*",
        parse_mode="Markdown"
    )


async def handle_consciousness_date(message: types.Message, date_str: str) -> None:
    """Обработка даты для анализа числа сознания."""
    if not analytics_service.validate_birth_date(date_str):
        await message.answer(
            "❌ **Неверный формат даты.**\n\n"
            "Введите дату в формате `dd.mm.yyyy`\n"
            "Например: `20.05.1997`",
            parse_mode="Markdown"
        )
        return
    
    user_id = message.from_user.id
    user_data[user_id]['birth_date'] = date_str
    
    # Выполняем анализ числа сознания
    await perform_consciousness_analysis(message, user_data[user_id])
    
    # Очищаем данные
    del user_data[user_id]


# === ЧИСЛО ДЕЙСТВИЯ ===

async def handle_action_query(message: types.Message, query: str) -> None:
    """Обработка запроса для анализа числа действия."""
    user_id = message.from_user.id
    user_data[user_id]['query'] = query
    user_data[user_id]['state'] = 'action_date'
    
    await message.answer(
        "**📅 Шаг 2 из 2: Дата рождения**\n\n"
        "Введите дату рождения в формате `dd.mm.yyyy`\n\n"
        "*Например: `20.05.1997`*",
        parse_mode="Markdown"
    )


async def handle_action_date(message: types.Message, date_str: str) -> None:
    """Обработка даты для анализа числа действия."""
    if not analytics_service.validate_birth_date(date_str):
        await message.answer(
            "❌ **Неверный формат даты.**\n\n"
            "Введите дату в формате `dd.mm.yyyy`\n"
            "Например: `20.05.1997`",
            parse_mode="Markdown"
        )
        return
    
    user_id = message.from_user.id
    user_data[user_id]['birth_date'] = date_str
    
    # Выполняем анализ числа действия
    await perform_action_analysis(message, user_data[user_id])
    
    # Очищаем данные
    del user_data[user_id]


# === ЧИСЛО ИМЕНИ ===

async def handle_name_query(message: types.Message, query: str) -> None:
    """Обработка запроса для анализа числа имени."""
    user_id = message.from_user.id
    user_data[user_id]['query'] = query
    user_data[user_id]['state'] = 'name_input'
    
    await message.answer(
        "**👤 Шаг 2 из 2: Имя**\n\n"
        "Введите ваше полное имя (кириллица или латиница)\n\n"
        "*Например: `Иван Петров` или `Ivan Petrov`*",
        parse_mode="Markdown"
    )


async def handle_name_input(message: types.Message, name: str) -> None:
    """Обработка имени для анализа числа имени."""
    if not analytics_service.validate_name(name):
        await message.answer(
            "❌ **Неверный формат имени.**\n\n"
            "Введите ваше полное имя (только буквы)\n"
            "Например: `Иван Петров`",
            parse_mode="Markdown"
        )
        return
    
    user_id = message.from_user.id
    user_data[user_id]['name'] = name
    
    # Выполняем анализ числа имени
    await perform_name_analysis(message, user_data[user_id])
    
    # Очищаем данные
    del user_data[user_id]


# === МАТРИЦА ===

async def handle_matrix_query(message: types.Message, query: str) -> None:
    """Обработка запроса для анализа матрицы."""
    user_id = message.from_user.id
    user_data[user_id]['query'] = query
    user_data[user_id]['state'] = 'matrix_date'
    
    await message.answer(
        "**📅 Шаг 2 из 2: Дата рождения**\n\n"
        "Введите дату рождения в формате `dd.mm.yyyy`\n\n"
        "*Например: `20.05.1997`*",
        parse_mode="Markdown"
    )


async def handle_matrix_date(message: types.Message, date_str: str) -> None:
    """Обработка даты для анализа матрицы."""
    if not analytics_service.validate_birth_date(date_str):
        await message.answer(
            "❌ **Неверный формат даты.**\n\n"
            "Введите дату в формате `dd.mm.yyyy`\n"
            "Например: `20.05.1997`",
            parse_mode="Markdown"
        )
        return
    
    user_id = message.from_user.id
    user_data[user_id]['birth_date'] = date_str
    
    # Выполняем анализ матрицы
    await perform_matrix_analysis(message, user_data[user_id])
    
    # Очищаем данные
    del user_data[user_id]


# === ПРАКТИКИ ===

async def handle_practices_query(message: types.Message, query: str) -> None:
    """Обработка запроса для поиска практик."""
    # Выполняем поиск практик
    await perform_practices_search(message, query)


# === ВЫПОЛНЕНИЕ АНАЛИЗОВ ===

async def perform_full_analysis(message: types.Message, data: Dict[str, Any]) -> None:
    """Выполнить полный анализ."""
    try:
        await message.answer("🔄 **Выполняю полный анализ...**", parse_mode="Markdown")
        
        # Выполняем анализ
        analysis = analytics_service.analyze_person(data['birth_date'], data['name'])
        
        # Получаем персонализированный отчет от OpenAI
        await get_personalized_report(
            message, 
            analysis_type="full",
            query=data['query'],
            birth_date=data['birth_date'],
            name=data['name'],
            analysis_data=analysis
        )
        
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка при выполнении анализа:** {str(e)}\n\n"
            "Пожалуйста, проверьте корректность введённых данных и попробуйте снова.",
            parse_mode="Markdown"
        )


async def perform_consciousness_analysis(message: types.Message, data: Dict[str, Any]) -> None:
    """Выполнить анализ числа сознания."""
    try:
        await message.answer("🔄 **Анализирую число сознания...**", parse_mode="Markdown")
        
        # Выполняем анализ только по дате
        analysis = analytics_service.analyze_person_date_only(data['birth_date'])
        
        # Получаем персонализированный отчет от OpenAI
        await get_personalized_report(
            message, 
            analysis_type="consciousness",
            query=data['query'],
            birth_date=data['birth_date'],
            name=None,
            analysis_data=analysis
        )
        
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка при выполнении анализа:** {str(e)}\n\n"
            "Пожалуйста, проверьте корректность введённых данных и попробуйте снова.",
            parse_mode="Markdown"
        )


async def perform_action_analysis(message: types.Message, data: Dict[str, Any]) -> None:
    """Выполнить анализ числа действия."""
    try:
        await message.answer("🔄 **Анализирую число действия...**", parse_mode="Markdown")
        
        # Выполняем анализ только по дате
        analysis = analytics_service.analyze_person_date_only(data['birth_date'])
        
        # Получаем персонализированный отчет от OpenAI
        await get_personalized_report(
            message, 
            analysis_type="action",
            query=data['query'],
            birth_date=data['birth_date'],
            name=None,
            analysis_data=analysis
        )
        
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка при выполнении анализа:** {str(e)}\n\n"
            "Пожалуйста, проверьте корректность введённых данных и попробуйте снова.",
            parse_mode="Markdown"
        )


async def perform_name_analysis(message: types.Message, data: Dict[str, Any]) -> None:
    """Выполнить анализ числа имени."""
    try:
        await message.answer("🔄 **Анализирую число имени...**", parse_mode="Markdown")
        
        # Создаем минимальный анализ только для имени
        from src.services.analytics.name_number import calc_name_number, get_name_interpretation
        from src.services.analytics.transliteration import normalize_name_for_calculation, is_cyrillic_text
        
        original_name = data['name'].strip()
        is_cyrillic = is_cyrillic_text(original_name)
        
        if is_cyrillic:
            latin_name = normalize_name_for_calculation(original_name)
        else:
            latin_name = normalize_name_for_calculation(original_name)
        
        name_number = calc_name_number(latin_name)
        name_interpretation = get_name_interpretation(name_number)
        
        analysis = {
            "input_data": {
                "original_name": original_name,
                "latin_name": latin_name,
                "is_cyrillic": is_cyrillic
            },
            "calculations": {
                "consciousness_number": None,
                "action_number": None,
                "name_number": name_number
            },
            "interpretations": {
                "consciousness_interpretation": None,
                "action_interpretation": None,
                "name_interpretation": name_interpretation
            },
            "matrix": {
                "digit_counts": {},
                "missing_digits": [],
                "strong_digits": [],
                "weak_digits": [],
                "analysis": "Анализ только по имени"
            },
            "exceptions": {
                "has_chs_chd_conflict": False
            }
        }
        
        # Получаем персонализированный отчет от OpenAI
        await get_personalized_report(
            message, 
            analysis_type="name",
            query=data['query'],
            birth_date=None,
            name=data['name'],
            analysis_data=analysis
        )
        
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка при выполнении анализа:** {str(e)}\n\n"
            "Пожалуйста, проверьте корректность введённых данных и попробуйте снова.",
            parse_mode="Markdown"
        )


async def perform_matrix_analysis(message: types.Message, data: Dict[str, Any]) -> None:
    """Выполнить анализ матрицы."""
    try:
        await message.answer("🔄 **Анализирую матрицу...**", parse_mode="Markdown")
        
        # Выполняем анализ только по дате
        analysis = analytics_service.analyze_person_date_only(data['birth_date'])
        
        # Получаем персонализированный отчет от OpenAI
        await get_personalized_report(
            message, 
            analysis_type="matrix",
            query=data['query'],
            birth_date=data['birth_date'],
            name=None,
            analysis_data=analysis
        )
        
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка при выполнении анализа:** {str(e)}\n\n"
            "Пожалуйста, проверьте корректность введённых данных и попробуйте снова.",
            parse_mode="Markdown"
        )


async def perform_practices_search(message: types.Message, query: str) -> None:
    """Выполнить поиск практик."""
    try:
        await message.answer("🔄 **Ищу подходящие практики...**", parse_mode="Markdown")
        
        # Получаем практики от OpenAI
        await get_practices_from_openai(message, query)
        
    except Exception as e:
        await message.answer(
            f"❌ **Ошибка при поиске практик:** {str(e)}\n\n"
            "Попробуйте сформулировать запрос по-другому.",
            parse_mode="Markdown"
        )


async def get_personalized_report(
    message: types.Message,
    analysis_type: str,
    query: str,
    birth_date: Optional[str],
    name: Optional[str],
    analysis_data: Dict[str, Any]
) -> None:
    """Получить персонализированный отчет от OpenAI."""
    try:
        settings = Settings.from_env()
        openai_service = OpenAIService(
            api_key=settings.openai_api_key,
            assistant_id=settings.openai_assistant_id
        )
        
        # Формируем JSON для OpenAI
        openai_data = {
            "analysis_type": analysis_type,
            "user_query": query,
            "birth_date": birth_date,
            "name": name,
            "analysis_data": analysis_data
        }
        
        # Проверяем, что analysis_data содержит нужные ключи
        if 'calculations' not in analysis_data:
            analysis_data['calculations'] = {}
        if 'interpretations' not in analysis_data:
            analysis_data['interpretations'] = {}
        if 'matrix' not in analysis_data:
            analysis_data['matrix'] = {}
        
        await message.answer("🤖 **Получаю персонализированный анализ...**", parse_mode="Markdown")
        
        
        # Получаем отчет от OpenAI
        report = await openai_service.analyze_person(
            birth_date=birth_date or "",
            full_name=name,
            analysis_data=analysis_data
        )
        
        # Отправляем отчет
        await send_long_message(message, report)
        
        # Предлагаем дополнительные действия
        await message.answer(
            "🎉 **Анализ завершен!**\n\n"
            "Для нового анализа выберите нужную команду из главного меню 👇",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"⚠️ OpenAI недоступен: {e}")
        await message.answer(
            "❌ **Сервис анализа временно недоступен.**\n\n"
            "Попробуйте позже или обратитесь к администратору.",
            parse_mode="Markdown"
        )


async def get_practices_from_openai(message: types.Message, query: str) -> None:
    """Получить практики от OpenAI."""
    try:
        settings = Settings.from_env()
        openai_service = OpenAIService(
            api_key=settings.openai_api_key,
            assistant_id=settings.openai_assistant_id
        )
        
        # Получаем практики от OpenAI с правильным промптом
        practices = await openai_service.search_practices(query)
        
        # Отправляем практики
        await send_long_message(message, practices)
        
        # Предлагаем дополнительные действия
        await message.answer(
            "🎉 **Поиск завершен!**\n\n"
            "Для нового поиска выберите нужную команду из главного меню 👇",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        print(f"⚠️ OpenAI недоступен: {e}")
        await message.answer(
            "❌ **Сервис поиска практик временно недоступен.**\n\n"
            "Попробуйте позже или обратитесь к администратору.",
            parse_mode="Markdown"
        )
