"""src/handlers/analyze.py
Обработчик для выполнения полного анализа пользователя.
"""
from __future__ import annotations

from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.services.analytics.analytics_service import AnalyticsService

router = Router()
analytics_service = AnalyticsService()


@router.message()
async def perform_analysis(message: types.Message) -> None:
    """Выполнить полный анализ пользователя."""
    text = message.text.strip()
    
    # Пытаемся извлечь дату и имя из сообщения
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) < 2:
        await message.answer(
            "❌ Недостаточно данных для анализа.\n\n"
            "Пожалуйста, введите:\n"
            "• Дату рождения в формате dd.mm.yyyy\n"
            "• Полное имя\n\n"
            "Например:\n"
            "29.02.1988\n"
            "Иван Петров"
        )
        return
    
    # Ищем дату и имя
    birth_date = None
    full_name = None
    
    for line in lines:
        if analytics_service.validate_birth_date(line):
            birth_date = line
        elif analytics_service.validate_name(line):
            full_name = line
    
    if not birth_date or not full_name:
        await message.answer(
            "❌ Не удалось найти корректные дату рождения и имя.\n\n"
            "Пожалуйста, проверьте формат:\n"
            "• **Дата:** dd.mm.yyyy (например, 15.03.1990)\n"
            "• **Имя:** Полное имя (например, Иван Петров)",
            parse_mode="Markdown"
        )
        return
    
    try:
        # Выполняем анализ
        await message.answer("🔄 Выполняю расчёты...")
        
        analysis = analytics_service.analyze_person(birth_date, full_name)
        
        # Формируем отчёт
        report = _format_analysis_report(analysis)
        
        # Создаём клавиатуру для дополнительных действий
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Подробная Матрица", callback_data=f"matrix_{message.from_user.id}")],
            [InlineKeyboardButton(text="🔄 Новый анализ", callback_data="new_analysis")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
        ])
        
        await message.answer(report, parse_mode="Markdown", reply_markup=keyboard)
        
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
    report = f"# 🔮 Персональный анализ по системе Миланы Тарба\n\n"
    
    # Вводные данные
    report += f"## 📋 Вводные данные\n"
    report += f"• **Имя:** {input_data['original_name']}\n"
    if input_data['is_cyrillic']:
        report += f"• **Латиницей:** {input_data['latin_name']}\n"
    report += f"• **Дата рождения:** {input_data['birth_date']}\n\n"
    
    # Ключевые числа
    report += f"## 🔢 Ключевые числа\n"
    report += f"• **Число Сознания (ЧС):** {calculations['consciousness_number']}\n"
    report += f"• **Число Действия (ЧД):** {calculations['action_number']}\n"
    report += f"• **Число Имени:** {calculations['name_number']}\n\n"
    
    # Матрица
    report += f"## 📊 Матрица энергий\n"
    if matrix['strong_digits']:
        report += f"• **Сильные энергии:** {', '.join(map(str, matrix['strong_digits']))} (100% и выше)\n"
    if matrix['weak_digits']:
        report += f"• **Слабые энергии:** {', '.join(map(str, matrix['weak_digits']))} (50%)\n"
    if matrix['missing_digits']:
        report += f"• **Отсутствующие энергии:** {', '.join(map(str, matrix['missing_digits']))}\n"
    report += f"• **Анализ:** {matrix['analysis']}\n\n"
    
    # Интерпретации
    report += f"## 💡 Интерпретация\n"
    report += f"• **Число Имени:** {interpretations['name_interpretation']}\n\n"
    
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
    await callback_query.message.edit_text(
        "🔄 Начинаем новый анализ!\n\n"
        "Введите ваши данные:\n"
        "• **Дата рождения:** dd.mm.yyyy\n"
        "• **Полное имя:** Ваше имя\n\n"
        "Например:\n"
        "29.02.1988\n"
        "Иван Петров",
        parse_mode="Markdown"
    )
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "help")
async def help_callback(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Помощь'."""
    help_text = (
        "📖 **Справка по анализу**\n\n"
        "**Что означают числа:**\n"
        "• **ЧС** - чего хочет ваша душа\n"
        "• **ЧД** - как вы действуете после 33 лет\n"
        "• **Число Имени** - энергия вашего имени\n"
        "• **Матрица** - какие энергии в вас заложены\n\n"
        "**Сила энергий в матрице:**\n"
        "• 1 цифра = 50% качества\n"
        "• 2 цифры = 100% качества\n"
        "• 3+ цифр = усиление на спад\n\n"
        "Все расчёты основаны на «Книге Знаний по Цифрологии»."
    )
    
    await callback_query.message.edit_text(help_text, parse_mode="Markdown")
    await callback_query.answer()
