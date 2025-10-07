"""src/handlers/main_menu.py
Главное меню бота с командами и навигацией.
"""
from __future__ import annotations

import asyncio
from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Главное меню с командами
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Старт")],
        [KeyboardButton(text="🔮 Получить полный разбор")],
        [KeyboardButton(text="🧠 Разбор числа сознания"), KeyboardButton(text="⚡ Разбор числа действия")],
        [KeyboardButton(text="📝 Разбор числа имени"), KeyboardButton(text="📊 Разбор матрицы")],
        [KeyboardButton(text="✨ Практика по запросу")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# Приветственное сообщение
WELCOME_MESSAGE = """🌟 **Добро пожаловать в Цифрового Психолога!**

Я помогу вам раскрыть тайны вашей личности через систему цифровой психологии Миланы Тарба.

**🔮 Что я умею:**
• **Полный разбор** - комплексный анализ всех показателей
• **Число сознания** - чего хочет ваша душа
• **Число действия** - как вы действуете после 33 лет
• **Число имени** - энергия вашего имени
• **Матрица** - какие энергии в вас заложены
• **Практики** - персональные рекомендации

**🧭 Режимы работы бота:**
• Personal — персональные разборы по вашим данным
• Chat — обезличенный режим вопросов по цифрологии (`/chat`)
• Marketing — идеи постов/рилс, прогревы, контент‑план (`/marketing`)
• Sales — ответы на возражения, воронки, офферы, тексты продаж (`/sales`)

Переключайтесь командами выше и задавайте произвольные запросы — я подстроюсь под выбранный режим.

Выберите нужный анализ из меню ниже 👇"""

# Описания результатов для каждой команды
ANALYSIS_DESCRIPTIONS = {
    "full": """🔮 **ПОЛНЫЙ РАЗБОР**

**Что вы получите:**
• Полный анализ всех показателей (ЧС, ЧД, Матрица, Число Имени)
• Персональные рекомендации по развитию
• Анализ совместимости энергий
• Практические советы для трансформации

**Время анализа:** 2-3 минуты
**Точность:** Максимальная (все алгоритмы)""",

    "consciousness": """🧠 **РАЗБОР ЧИСЛА СОЗНАНИЯ**

**Что вы получите:**
• Чего хочет ваша душа (только день рождения)
• Ваши истинные желания и стремления
• Рекомендации по духовному развитию
• Понимание внутренней мотивации

**Время анализа:** 1-2 минуты
**Основа:** День рождения""",

    "action": """⚡ **РАЗБОР ЧИСЛА ДЕЙСТВИЯ**

**Что вы получите:**
• Как вы действуете после 33 лет (вся дата рождения)
• Ваш стиль поведения и принятия решений
• Рекомендации по карьерному росту
• Понимание ваших действий

**Время анализа:** 1-2 минуты
**Основа:** Полная дата рождения""",

    "name": """📝 **РАЗБОР ЧИСЛА ИМЕНИ**

**Что вы получите:**
• Энергию вашего имени
• Как имя влияет на вашу судьбу
• Рекомендации по использованию имени
• Понимание энергетики имени

**Время анализа:** 1-2 минуты
**Основа:** Ваше имя""",

    "matrix": """📊 **РАЗБОР МАТРИЦЫ**

**Что вы получите:**
• Какие энергии в вас заложены (вся дата рождения)
• Сильные и слабые стороны
• Отсутствующие энергии
• Рекомендации по балансировке

**Время анализа:** 1-2 минуты
**Основа:** Полная дата рождения""",

    "practices": """✨ **ПРАКТИКА ПО ЗАПРОСУ**

**Что вы получите:**
• Персональные практики по вашему запросу
• Упражнения для развития нужных качеств
• Конкретные техники трансформации
• Пошаговые инструкции

**Время поиска:** 30 секунд
**Основа:** Ваш запрос"""
}


@router.message(CommandStart())
async def on_start(message: types.Message) -> None:
    """Обработчик команды /start - главное меню."""
    # Отправляем картинку
    try:
        import os
        photo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "media", "kartinka.jpg")
        await message.answer_photo(
            photo=open(photo_path, 'rb'),
            caption=WELCOME_MESSAGE,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard
        )
    except Exception as e:
        # Если картинка не найдена, отправляем только текст
        print(f"⚠️ Не удалось загрузить картинку: {e}")
        await message.answer(
            WELCOME_MESSAGE,
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard
        )


@router.message(lambda message: message.text == "🔮 Получить полный разбор")
async def full_analysis_start(message: types.Message) -> None:
    """Начало полного анализа."""
    from .step_handler import user_data
    
    user_id = message.from_user.id
    user_data[user_id] = {'state': 'full_analysis_query'}
    
    await message.answer(
        ANALYSIS_DESCRIPTIONS["full"],
        parse_mode="Markdown"
    )
    
    # Запрашиваем запрос пользователя
    await message.answer(
        "**📝 Шаг 1 из 3: Ваш запрос**\n\n"
        "Опишите, что вас интересует или беспокоит:\n"
        "• Какие вопросы у вас есть?\n"
        "• Что хотите узнать о себе?\n"
        "• Какие сферы жизни вас волнуют?\n\n"
        "*Например: \"Хочу понять свои сильные стороны и как лучше строить карьеру\"*",
        parse_mode="Markdown"
    )


@router.message(lambda message: message.text == "🧠 Разбор числа сознания")
async def consciousness_analysis_start(message: types.Message) -> None:
    """Начало анализа числа сознания."""
    from .step_handler import user_data
    
    user_id = message.from_user.id
    user_data[user_id] = {'state': 'consciousness_query'}
    
    await message.answer(
        ANALYSIS_DESCRIPTIONS["consciousness"],
        parse_mode="Markdown"
    )
    
    # Запрашиваем запрос пользователя
    await message.answer(
        "**📝 Шаг 1 из 2: Ваш запрос**\n\n"
        "Опишите, что вас интересует в плане внутренних желаний:\n"
        "• Чего вы хотите от жизни?\n"
        "• Какие у вас есть мечты?\n"
        "• Что вас мотивирует?\n\n"
        "*Например: \"Хочу понять, чего на самом деле хочет моя душа\"*",
        parse_mode="Markdown"
    )


@router.message(lambda message: message.text == "⚡ Разбор числа действия")
async def action_analysis_start(message: types.Message) -> None:
    """Начало анализа числа действия."""
    from .step_handler import user_data
    
    user_id = message.from_user.id
    user_data[user_id] = {'state': 'action_query'}
    
    await message.answer(
        ANALYSIS_DESCRIPTIONS["action"],
        parse_mode="Markdown"
    )
    
    # Запрашиваем запрос пользователя
    await message.answer(
        "**📝 Шаг 1 из 2: Ваш запрос**\n\n"
        "Опишите, что вас интересует в плане действий:\n"
        "• Как вы принимаете решения?\n"
        "• Какие у вас есть проблемы с действиями?\n"
        "• Что хотите изменить в поведении?\n\n"
        "*Например: \"Хочу понять, почему я не могу принимать быстрые решения\"*",
        parse_mode="Markdown"
    )


@router.message(lambda message: message.text == "📝 Разбор числа имени")
async def name_analysis_start(message: types.Message) -> None:
    """Начало анализа числа имени."""
    from .step_handler import user_data
    
    user_id = message.from_user.id
    user_data[user_id] = {'state': 'name_query'}
    
    await message.answer(
        ANALYSIS_DESCRIPTIONS["name"],
        parse_mode="Markdown"
    )
    
    # Запрашиваем запрос пользователя
    await message.answer(
        "**📝 Шаг 1 из 2: Ваш запрос**\n\n"
        "Опишите, что вас интересует в плане имени:\n"
        "• Как имя влияет на вашу жизнь?\n"
        "• Стоит ли менять имя?\n"
        "• Какая энергия в вашем имени?\n\n"
        "*Например: \"Хочу понять, как мое имя влияет на мою судьбу\"*",
        parse_mode="Markdown"
    )


@router.message(lambda message: message.text == "📊 Разбор матрицы")
async def matrix_analysis_start(message: types.Message) -> None:
    """Начало анализа матрицы."""
    from .step_handler import user_data
    
    user_id = message.from_user.id
    user_data[user_id] = {'state': 'matrix_query'}
    
    await message.answer(
        ANALYSIS_DESCRIPTIONS["matrix"],
        parse_mode="Markdown"
    )
    
    # Запрашиваем запрос пользователя
    await message.answer(
        "**📝 Шаг 1 из 2: Ваш запрос**\n\n"
        "Опишите, что вас интересует в плане энергий:\n"
        "• Какие у вас сильные стороны?\n"
        "• Что нужно развивать?\n"
        "• Какие энергии отсутствуют?\n\n"
        "*Например: \"Хочу понять свои сильные и слабые стороны\"*",
        parse_mode="Markdown"
    )


@router.message(lambda message: message.text == "✨ Практика по запросу")
async def practices_start(message: types.Message) -> None:
    """Начало поиска практик."""
    from .step_handler import user_data
    
    user_id = message.from_user.id
    user_data[user_id] = {'state': 'practices_query'}
    
    await message.answer(
        ANALYSIS_DESCRIPTIONS["practices"],
        parse_mode="Markdown"
    )
    
    # Запрашиваем запрос пользователя
    await message.answer(
        "**📝 Ваш запрос**\n\n"
        "Опишите, какие практики вам нужны:\n"
        "• Что хотите развить в себе?\n"
        "• Какие проблемы решить?\n"
        "• Какие качества улучшить?\n\n"
        "*Например: \"Хочу стать более уверенным в себе\" или \"Нужны практики для развития лидерства\"*",
        parse_mode="Markdown"
    )


@router.message(lambda message: message.text == "🚀 Старт")
async def start_button_handler(message: types.Message):
    """Обработчик кнопки Старт."""
    await on_start(message)

@router.message(lambda message: message.text == "❓ Помощь")
async def show_help(message: types.Message) -> None:
    """Показать справку."""
    help_text = """📖 **СПРАВКА ПО ИСПОЛЬЗОВАНИЮ БОТА**

**📅 Формат даты рождения:**
• Обязательно: dd.mm.yyyy
• Примеры: 15.03.1990, 01.01.2000

**👤 Формат имени:**
• Можно на кириллице: *Иван Петров*
• Можно на латинице: *Ivan Petrov*
• Полное имя (имя + фамилия)

**🔮 Что означают числа:**
• **ЧС** - чего хочет ваша душа (только день рождения)
• **ЧД** - как вы действуете после 33 лет (вся дата рождения)
• **Число Имени** - энергия вашего имени (только имя)
• **Матрица** - какие энергии в вас заложены (вся дата рождения)

**Сила энергий в матрице:**
• 1 цифра = 50% качества
• 2 цифры = 100% качества
• 3+ цифр = усиление на спад

*Все расчёты основаны на «Книге Знаний по Цифрологии» системы Миланы Тарба.*"""
    
    await message.answer(help_text, parse_mode="Markdown")
