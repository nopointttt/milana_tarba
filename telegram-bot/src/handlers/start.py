"""src/handlers/start.py
Обработчик /start: приветствие и запрос входных данных согласно спецификации.
"""
from __future__ import annotations
import asyncio

from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.analytics.analytics_service import AnalyticsService
from src.services.user_service import UserService
from src.services.analytics_storage import AnalyticsStorageService
from src.services.openai_service import OpenAIService
from src.db.connection import get_db_manager
from src.config import Settings

router = Router()
analytics_service = AnalyticsService()


WELCOME = (
    "Привет! Я твой ассистент по цифровой психологии по системе Миланы Тарба.\n\n"
    "Введите дату рождения в формате: 20.05.1997"
)

# Клавиатура только с помощью
input_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Помощь")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


@router.message(CommandStart())
async def on_start(message: types.Message) -> None:
    """Обработчик команды /start."""
    await message.answer(
        WELCOME,
        reply_markup=input_keyboard
    )




@router.message(lambda message: message.text == "Помощь")
async def show_help(message: types.Message) -> None:
    """Показать справку."""
    help_text = (
        "**📖 СПРАВКА ПО ИСПОЛЬЗОВАНИЮ БОТА**\n\n"
        "**📅 Формат даты рождения:**\n"
        "• Обязательно: dd.mm.yyyy\n"
"• Примеры: 15.03.1990, 01.01.2000\n\n"
        "**👤 Формат имени:**\n"
        "• Можно на кириллице: *Иван Петров*\n"
        "• Можно на латинице: *Ivan Petrov*\n"
        "• Полное имя (имя + фамилия)\n\n"
        "**🔮 Что я рассчитываю:**\n"
        "• **Число Сознания (ЧС)**\n"
        "• **Число Действия (ЧД)**\n"
        "• **Матрица энергий**\n"
        "• **Число Имени**\n\n"
        "*Все расчёты основаны на «Книге Знаний по Цифрологии» системы Миланы Тарба.*"
    )
    
    await message.answer(help_text, parse_mode="Markdown")


# Хранилище для временных данных пользователей
user_data = {}


def convert_markdown_to_html(text: str) -> str:
    """Конвертирует Markdown в HTML для Telegram."""
    # Убираем неподдерживаемые HTML теги
    text = text.replace('<br>', '\n')
    text = text.replace('<br/>', '\n')
    text = text.replace('<br />', '\n')
    text = text.replace('<p>', '')
    text = text.replace('</p>', '\n\n')
    text = text.replace('<div>', '')
    text = text.replace('</div>', '\n')
    
    # Заменяем заголовки
    text = text.replace('### ', '<b>')
    text = text.replace('## ', '<b>')
    text = text.replace('# ', '<b>')
    
    # Закрываем заголовки
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('<b>') and not line.endswith('</b>'):
            # Ищем конец строки или следующий заголовок
            if i + 1 < len(lines) and (lines[i + 1].startswith('<b>') or lines[i + 1].strip() == ''):
                lines[i] = line + '</b>'
            elif line.strip() and not line.endswith('</b>'):
                lines[i] = line + '</b>'
    
    text = '\n'.join(lines)
    
    # Заменяем жирный текст
    text = text.replace('**', '<b>')
    # Исправляем двойные теги
    text = text.replace('<b><b>', '<b>')
    text = text.replace('</b></b>', '</b>')
    
    # Заменяем курсив
    text = text.replace('*', '<i>')
    # Исправляем двойные теги
    text = text.replace('<i><i>', '<i>')
    text = text.replace('</i></i>', '</i>')
    
    # Заменяем списки
    text = text.replace('• ', '• ')
    
    # Очищаем лишние переносы строк
    text = text.replace('\n\n\n', '\n\n')
    
    return text.strip()


async def send_long_message(message: types.Message, text: str, max_length: int = 4000) -> None:
    """Отправляет длинное сообщение частями."""
    if len(text) <= max_length:
        await message.answer(text, parse_mode="Markdown")
        return
    
    # Разбиваем по разделам
    sections = text.split('\n\n')
    current_message = ""
    
    for section in sections:
        # Если добавление раздела превысит лимит
        if len(current_message) + len(section) + 2 > max_length:
            # Отправляем текущее сообщение
            if current_message.strip():
                await message.answer(current_message.strip(), parse_mode="Markdown")
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
        await message.answer(current_message.strip(), parse_mode="Markdown")

@router.message()
async def process_user_input(message: types.Message) -> None:
    """Обработка ввода пользователя."""
    text = message.text.strip()
    user_id = message.from_user.id
    
    # Проверяем, есть ли у пользователя сохранённые данные
    if user_id not in user_data:
        user_data[user_id] = {}
    
    # Проверка на формат даты (если не ввели дату)
    if analytics_service.validate_birth_date(text) and 'birth_date' not in user_data[user_id]:
        user_data[user_id]['birth_date'] = text
        
        await message.answer(
            f"Спасибо дата принята: {text}\n"
            "Введите имя",
            parse_mode="Markdown"
        )
        return
    
    # Проверка на имя (если есть дата, но нет имени)
    if analytics_service.validate_name(text) and 'birth_date' in user_data[user_id] and 'name' not in user_data[user_id]:
        user_data[user_id]['name'] = text
        
        await message.answer(
            "Ваши данные приняты начинаем анализ",
            parse_mode="Markdown"
        )
        
        # Выполняем анализ
        await perform_analysis_with_data(message, user_data[user_id]['birth_date'], text)
        # Очищаем данные после анализа
        del user_data[user_id]
        return
    
    # Если не распознали формат
    if 'birth_date' not in user_data[user_id]:
        await message.answer(
            "❌ **Неверный формат даты.**\n\n"
            "Введите дату в формате dd.mm.yyyy\n"
"Например: 20.05.1997",
            parse_mode="Markdown"
        )
    elif 'name' not in user_data[user_id]:
        await message.answer(
            "❌ **Неверный формат имени.**\n\n"
            "Введите ваше имя (одно слово)\n"
            "Например: *Иван*",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "❌ **Не удалось распознать формат ввода.**\n\n"
            "Нажмите `/start` для начала заново.",
            parse_mode="Markdown"
        )


async def perform_analysis_with_data(message: types.Message, birth_date: str, name: str = None) -> None:
    """Выполнить анализ с готовыми данными."""
    try:
        # Выполняем анализ
        await message.answer("🔄 **Выполняю расчёты...**", parse_mode="Markdown")
        
        if name:
            analysis = analytics_service.analyze_person(birth_date, name)
        else:
            # Анализ только по дате рождения
            analysis = analytics_service.analyze_person_date_only(birth_date)
        
        # Сохраняем результат в базу данных
        try:
            db_manager = get_db_manager()
            async with db_manager.get_session() as session:
                # Получаем или создаём пользователя
                user_service = UserService(session)
                user = await user_service.get_or_create_user(
                    telegram_user_id=message.from_user.id,
                    username=message.from_user.username,
                    full_name=message.from_user.full_name
                )
                
                # Debug: проверяем user.id
                print(f"🔍 DEBUG: user.id = {user.id}, user.telegram_user_id = {user.telegram_user_id}")
                
                if user.id is None:
                    print("❌ ERROR: user.id is None! Committing and refreshing...")
                    await session.commit()
                    await session.refresh(user)
                    print(f"🔍 DEBUG after refresh: user.id = {user.id}")
                
                # Сохраняем анализ
                storage_service = AnalyticsStorageService(session)
                from datetime import date
                from src.db.models import ReportStatus
                
                # Парсим дату
                day, month, year = map(int, birth_date.split('.'))
                birth_date_obj = date(year, month, day)
                
                await storage_service.save_analysis_result(
                    user_id=user.id,
                    full_name=name or "Не указано",
                    birth_date=birth_date_obj,
                    analysis_result=analysis,
                    status=ReportStatus.DONE
                )
                
        except Exception as db_error:
            # Логируем ошибку, но не прерываем выполнение
            print(f"⚠️ Ошибка сохранения в БД: {db_error}")
        
        # Пытаемся получить персонализированный анализ от OpenAI
        try:
            settings = Settings.from_env()
            openai_service = OpenAIService(
                api_key=settings.openai_api_key,
                assistant_id=settings.openai_assistant_id
            )
            
            # Получаем персонализированный анализ
            await message.answer("🤖 **Получаю персонализированный анализ от цифрового психолога...**", parse_mode="Markdown")
            
            personalized_report = await openai_service.analyze_person(
                birth_date=birth_date,
                full_name=name,
                analysis_data=analysis
            )
            
            # Разбиваем длинные сообщения на части (используем Markdown)
            await send_long_message(message, personalized_report)
            
        except Exception as e:
            # Если OpenAI недоступен, используем стандартный отчёт
            print(f"⚠️ OpenAI недоступен: {e}")
            report = _format_analysis_report(analysis)
            await message.answer(report, parse_mode="Markdown")
        
        # Создаём клавиатуру для дополнительных действий
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Подробная Матрица", callback_data=f"matrix_{message.from_user.id}")],
            [InlineKeyboardButton(text="🔄 Новый анализ", callback_data="new_analysis")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
        ])
        
        await message.answer("Выберите дополнительное действие:", reply_markup=keyboard)
        
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при выполнении анализа: {str(e)}\n\n"
            "Пожалуйста, проверьте корректность введённых данных и попробуйте снова."
        )


def _format_analysis_report(analysis: dict) -> str:
    """Форматировать отчёт анализа."""
    input_data = analysis["input_data"]
    calculations = analysis["calculations"]
    matrix = analysis["matrix"]
    interpretations = analysis["interpretations"]
    
    # Заголовок
    report = f"**🔮 ПЕРСОНАЛЬНЫЙ АНАЛИЗ ПО СИСТЕМЕ МИЛАНЫ ТАРБА**\n\n"
    
    # Вводные данные
    report += f"**📋 ВВОДНЫЕ ДАННЫЕ**\n"
    if input_data.get('has_name', True):  # Если есть имя
        report += f"• **Имя:** *{input_data['original_name']}*\n"
        if input_data.get('is_cyrillic', False):
            report += f"• **Латиницей:** *{input_data['latin_name']}*\n"
    else:
        report += f"• **Имя:** *Не указано (анализ только по дате рождения)*\n"
    report += f"• **Дата рождения:** {input_data['birth_date']}\n\n"
    
    # Ключевые числа
    report += f"**🔢 КЛЮЧЕВЫЕ ЧИСЛА**\n"
    report += f"• **Число Сознания (ЧС):** {calculations['consciousness_number']}\n"
    report += f"• **Число Действия (ЧД):** {calculations['action_number']}\n"
    if calculations['name_number'] is not None:
        report += f"• **Число Имени:** {calculations['name_number']}\n"
    else:
        report += f"• **Число Имени:** *Не рассчитано (имя не указано)*\n"
    report += "\n"
    
    # Матрица
    report += f"**📊 МАТРИЦА ЭНЕРГИЙ**\n"
    if matrix['strong_digits']:
        report += f"• **Сильные энергии:** {', '.join(map(str, matrix['strong_digits']))} (100% и выше)\n"
    if matrix['weak_digits']:
        report += f"• **Слабые энергии:** {', '.join(map(str, matrix['weak_digits']))} (50%)\n"
    if matrix['missing_digits']:
        report += f"• **Отсутствующие энергии:** {', '.join(map(str, matrix['missing_digits']))}\n"
    report += f"• **Анализ:** {matrix['analysis']}\n\n"
    
    # Интерпретации
    report += f"**💡 ИНТЕРПРЕТАЦИЯ**\n"
    if 'consciousness_interpretation' in interpretations:
        report += f"• **ЧС:** {interpretations['consciousness_interpretation']}\n"
    if 'action_interpretation' in interpretations:
        report += f"• **ЧД:** {interpretations['action_interpretation']}\n"
    if 'name_interpretation' in interpretations:
        report += f"• **Число Имени:** {interpretations['name_interpretation']}\n"
    report += "\n"
    
    # Исключения
    if analysis['exceptions']['has_chs_chd_conflict']:
        report += f"⚠️ **Особое внимание:** Обнаружен внутренний конфликт между ЧС и ЧД\n\n"
    
    # Дисклеймер
    report += f"*Анализ выполнен на базе правил из «Книги Знаний по Цифрологии». "
    report += f"Результат — не приговор, а карта возможностей.*"
    
    return report


@router.callback_query(lambda c: c.data == "new_analysis")
async def new_analysis_callback(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Новый анализ'."""
    # Очищаем данные пользователя
    user_id = callback_query.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    
    await callback_query.message.edit_text(
        "🔄 **Начинаем новый анализ!**\n\n"
        "**Введите ваши данные:**\n"
        "• **Дата рождения:** `dd.mm.yyyy`\n"
        "• **Полное имя:** Ваше имя\n\n"
        "**Например:**\n"
        "`29.02.1988`\n"
        "*Иван Петров*",
        parse_mode="Markdown"
    )
    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith("analyze_date_"))
async def analyze_date_callback(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Анализ по дате'."""
    user_id = int(callback_query.data.split("_")[2])
    
    if user_id in user_data and 'birth_date' in user_data[user_id]:
        birth_date = user_data[user_id]['birth_date']
        await perform_analysis_with_data(callback_query.message, birth_date, None)
        # Очищаем данные после анализа
        del user_data[user_id]
    else:
        await callback_query.answer("❌ **Данные не найдены. Начните заново с /start**", parse_mode="Markdown")
    
    await callback_query.answer()


@router.callback_query(lambda c: c.data.startswith("add_name_"))
async def add_name_callback(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Добавить имя'."""
    user_id = int(callback_query.data.split("_")[2])
    
    # Устанавливаем флаг ожидания имени
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['waiting_for_name'] = True
    
    await callback_query.message.edit_text(
        "👤 **Введите только ваше полное имя** (кириллица или латиница):\n\n"
        "**Например:** *Иван Петров*\n"
        "**или:** *Ivan Petrov*",
        parse_mode="Markdown"
    )
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "help")
async def help_callback(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Помощь'."""
    help_text = (
        "📖 **Справка по анализу**\n\n"
        "**Что означают числа:**\n"
        "• **ЧС** - чего хочет ваша душа (только день рождения)\n"
        "• **ЧД** - как вы действуете после 33 лет (вся дата рождения)\n"
        "• **Число Имени** - энергия вашего имени (только имя)\n"
        "• **Матрица** - какие энергии в вас заложены (вся дата рождения)\n\n"
        "**Сила энергий в матрице:**\n"
        "• 1 цифра = 50% качества\n"
        "• 2 цифры = 100% качества\n"
        "• 3+ цифр = усиление на спад\n\n"
        "Все расчёты основаны на «Книге Знаний по Цифрологии»."
    )
    
    await callback_query.message.edit_text(help_text, parse_mode="Markdown")
    await callback_query.answer()
