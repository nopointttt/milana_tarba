"""src/handlers/context_handler.py
Обработчик контекстного общения с ботом.
"""
from __future__ import annotations

import json
from typing import Dict, List, Any
from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from src.services.openai_context_service import OpenAIContextService
from src.config import Settings
from src.db.connection import get_db_manager
from src.services.analytics.chs import calc_chs
from src.services.analytics.chd import calc_chd
from src.services.analytics.name_number import calc_name_number
from src.services.analytics.matrix import build_matrix
from datetime import datetime

router = Router()

# Простая клавиатура
simple_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# Кнопки для ввода данных
data_input_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📝 Ввести данные", callback_data="input_data")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ]
)

# Кнопки для управления данными
data_management_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить данные", callback_data="update_data")],
        [InlineKeyboardButton(text="🗑️ Очистить дополнительные данные", callback_data="clear_additional")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
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

# Приветственное сообщение
WELCOME_MESSAGE = """🌟 ПРИВЕТ! Я ТВОЙ ЦИФРОВОЙ ПСИХОЛОГ ПО СИСТЕМЕ МИЛАНЫ ТАРБА.

Я помогу тебе понять себя через анализ твоей даты рождения и имени. 

🔮 ЧТО Я УМЕЮ:
• Рассчитывать ЧС, ЧД, Матрицу, Число Имени
• Давать персональные рекомендации и прогнозы
• Подбирать практики под твои запросы
• Анализировать совместимость и предназначение

📝 ДЛЯ НАЧАЛА МНЕ НУЖНЫ ТВОИ ДАННЫЕ:
• Имя (только на английском, например: Ivan)
• Дата рождения (dd.mm.yyyy)

После ввода данных ты сможешь просто писать запросы, и я буду использовать твои сохраненные данные!"""


@router.message(CommandStart())
async def on_start(message: types.Message) -> None:
    """Обработчик команды /start."""
    user_id = message.from_user.id
    
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
            reply_markup=data_input_keyboard,
        )


@router.message(lambda message: message.text == "❓ Помощь")
async def show_help(message: types.Message) -> None:
    """Показать справку."""
    help_text = """📖 СПРАВКА

💬 КАК ОБЩАТЬСЯ:
Просто пиши мне естественно, как другу. Я понимаю твои вопросы и запросы.

📅 ФОРМАТ ДАТЫ РОЖДЕНИЯ:
• Обязательно: dd.mm.yyyy
• Примеры: 15.03.1990, 01.01.2000

👤 ФОРМАТ ИМЕНИ:
• Только на английском языке: Ivan
• Только имя (без фамилии)
• Примеры: John, Maria, Alex, Anna, Michael

🔮 ЧТО ОЗНАЧАЮТ ЧИСЛА:
• ЧС - чего хочет твоя душа (только день рождения)
• ЧД - как ты действуешь после 33 лет (вся дата рождения)
• Число Имени - энергия твоего имени
• Матрица - какие энергии в тебе заложены

✨ ПРАКТИКИ:
Я подберу персональные практики под любой твой запрос.

Все расчеты основаны на «Книге Знаний по Цифрологии» системы Миланы Тарба."""
    
    await message.answer(help_text)


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
    lines = [line.strip() for line in message_text.strip().split('\n') if line.strip()]
    
    # Поддержка многострочного ввода (2 строки)
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
    lines = [line.strip() for line in message_text.strip().split('\n') if line.strip()]
    
    # Поддержка многострочного ввода (2 строки)
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

def calculate_user_analytics(name: str, birth_date: str) -> Dict[str, Any]:
    """Рассчитывает аналитику пользователя (ЧС, ЧД, ЧИ, матрица)."""
    try:
        # Парсим дату
        date_obj = datetime.strptime(birth_date, "%d.%m.%Y")
        
        # Рассчитываем ЧС и ЧД
        chs = calc_chs(date_obj)
        chd = calc_chd(date_obj)
        
        # Рассчитываем ЧИ
        name_number = calc_name_number(name)
        
        # Строим матрицу
        matrix = build_matrix(date_obj)
        
        # Извлекаем энергии из матрицы с описаниями
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
        
        for i in range(1, 10):
            count = matrix.digit_counts.get(i, 0)
            if count > 0:
                description = energy_descriptions.get(str(i), "")
                matrix_energies[str(i)] = f"{count} ({description})"
        
        
        return {
            "chs": chs,
            "chd": chd,
            "name_number": name_number,
            "matrix_energies": matrix_energies
        }
    except Exception as e:
        print(f"Ошибка при расчете аналитики: {e}")
        return {
            "chs": None,
            "chd": None,
            "name_number": None,
            "matrix_energies": {}
        }

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
    
    # Очищаем невалидные данные, если они есть
    if user_id in user_data and not _has_valid_user_data(user_id):
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
            for i in range(len(parts)):
                # Вариант 1: "Имя Дата" - берем последнюю часть как дату
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
                
                # Вариант 2: "Дата Имя" - берем первую часть как дату
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
            
            await message.answer("✅ Дата рождения сохранена! Теперь введите ваше имя (только на английском):")
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
            
            await message.answer("✅ Имя сохранено! Теперь введите дату рождения (dd.mm.yyyy):")
            return True
    
    return False


def is_date_format(text: str) -> bool:
    """Проверяет, является ли текст валидной датой."""
    import re
    from datetime import datetime
    
    date_patterns = [
        r'\d{1,2}\.\d{1,2}\.\d{4}',
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{1,2}-\d{1,2}-\d{4}',
        r'\d{1,2}\s+\d{1,2}\s+\d{4}'
    ]
    
    for pattern in date_patterns:
        if re.match(pattern, text):
            # Проверяем валидность даты
            try:
                # Заменяем разделители на точки для парсинга
                normalized_date = re.sub(r'[/\s-]', '.', text)
                datetime.strptime(normalized_date, '%d.%m.%Y')
                return True
            except ValueError:
                continue
    return False


def is_name_format(text: str) -> bool:
    """Проверяет, является ли текст именем."""
    # Простая проверка: только буквы, может содержать пробелы, длина 2-50 символов
    if not text or not text.strip():
        return False
    
    text = text.strip()
    
    # Проверяем, что все символы - буквы или пробелы
    if not all(c.isalpha() or c.isspace() for c in text):
        return False
    
    # Проверяем, что есть хотя бы одна буква
    if not any(c.isalpha() for c in text):
        return False
    
    # Проверяем длину (увеличиваем лимит для составных имен)
    if len(text) < 2 or len(text) > 50:
        return False
    
    return True


async def validate_and_save_data(message: types.Message, name: str, birth_date: str) -> bool:
    """Валидирует и сохраняет данные пользователя."""
    user_id = message.from_user.id
    
    # Валидируем имя
    if not is_name_format(name):
        await message.answer("❌ Имя должно быть только на английском языке, одно слово. Например: Ivan")
        return True
    
    # Валидируем дату
    if not is_date_format(birth_date):
        await message.answer("❌ Неверный формат даты. Используйте dd.mm.yyyy, например: 20.05.1997")
        return True
    
    # Нормализуем дату
    try:
        from datetime import datetime
        date_formats = ["%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d %m %Y"]
        
        for fmt in date_formats:
            try:
                d = datetime.strptime(birth_date, fmt)
                birth_date = d.strftime("%d.%m.%Y")
                break
            except ValueError:
                continue
        else:
            raise ValueError("Неподдерживаемый формат даты")
    except ValueError:
        await message.answer("❌ Неверный формат даты. Используйте dd.mm.yyyy, например: 20.05.1997")
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
    
    # Проверяем, вводит ли пользователь данные
    if await handle_data_input(message):
        return
    
    # Проверяем, были ли данные только что обновлены
    if user_id in data_just_updated and data_just_updated[user_id]:
        # Сбрасываем флаг
        data_just_updated[user_id] = False
        # Не обрабатываем сообщение как запрос к OpenAI
        return
    
    # Проверяем, есть ли у пользователя сохраненные данные
    if user_id not in user_data:
        await message.answer(
            "❌ Сначала введите ваши данные! Нажмите кнопку '📝 Ввести данные'",
            reply_markup=data_input_keyboard
        )
        return
    
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
                if user_id not in additional_data:
                    additional_data[user_id] = []
                additional_data[user_id].append(additional_info)
                
                # Формируем сообщение с дополнительными данными
                user_data_info = user_data[user_id]
                analytics = user_data_info.get('analytics', {})
                enhanced_message = f"Пользователь: {user_message}\n\nОсновные данные пользователя:\nИмя: {user_data_info['name']}\nДата рождения: {user_data_info['birth_date']}\nЧС: {analytics.get('chs', 'N/A')}\nЧД: {analytics.get('chd', 'N/A')}\nЧИ: {analytics.get('name_number', 'N/A')}\nМатрица энергий: {analytics.get('matrix_energies', {})}\n\nДополнительные данные для сравнения:\nИмя: {additional_info['name']}\nДата рождения: {additional_info['birth_date']}"
            else:
                # Обычное сообщение с основными данными
                user_data_info = user_data[user_id]
                analytics = user_data_info.get('analytics', {})
                enhanced_message = f"Пользователь: {user_message}\n\nДанные пользователя:\nИмя: {user_data_info['name']}\nДата рождения: {user_data_info['birth_date']}\nЧС: {analytics.get('chs', 'N/A')}\nЧД: {analytics.get('chd', 'N/A')}\nЧИ: {analytics.get('name_number', 'N/A')}\nМатрица энергий: {analytics.get('matrix_energies', {})}"
            
            
            # Обновляем статус
            await update_status_message(status_msg, "Обрабатываю запрос через ИИ...")
            
            # Обрабатываем сообщение
            response = await openai_service.process_message(
                user_message=enhanced_message,
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
    instruction_message = """📝 **Введите ваши данные:**

**1. Имя (только на английском):**
Например: Ivan, Maria, John

**2. Дата рождения:**
Формат: dd.mm.yyyy
Например: 20.05.1997

**Отправьте данные в одном сообщении:**
```
Ivan
20.05.1997
```

Или по отдельности:
• Сначала имя
• Потом дату рождения"""
    
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
        )


@router.callback_query(lambda c: c.data == "help")
async def handle_help_callback(callback_query: types.CallbackQuery) -> None:
    """Обработчик кнопки 'Помощь'."""
    await callback_query.answer()
    
    help_text = """📖 **СПРАВКА**

**💬 Как общаться:**
Просто пиши мне естественно, как другу. Я понимаю твои вопросы и запросы.

**📅 Формат даты рождения:**
• Обязательно: dd.mm.yyyy
• Примеры: 15.03.1990, 01.01.2000

**👤 Формат имени:**
• Только на английском языке
• Одно слово (без фамилии)
• Примеры: Ivan, Maria, John

**🔮 Что я умею:**
• Анализ по дате рождения и имени
• Прогнозы на год/месяц/день
• Анализ совместимости
• Советы по реализации
• Подбор персональных практик

**💡 Примеры запросов:**
• "Дай мне прогноз на год"
• "Расскажи про мою матрицу"
• "Нужны практики для уверенности"
• "Помоги с отношениями"
• "Что мое предназначение?"""
    
    await callback_query.message.edit_text(
        help_text,
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
        )


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
    
    data_message = f"""✅ **Ваши данные сохранены!**

👤 **Имя:** {name}
📅 **Дата рождения:** {birth_date}

🔢 **ВАШИ ЧИСЛА:**
• ЧС (Число Сознания): {analytics.get('chs', 'N/A')}
• ЧД (Число Действия): {analytics.get('chd', 'N/A')}
• ЧИ (Число Имени): {analytics.get('name_number', 'N/A')}

⚡ **МАТРИЦА ЭНЕРГИЙ:**"""
    
    # Добавляем матрицу энергий
    matrix_energies = analytics.get('matrix_energies', {})
    if matrix_energies:
        for energy, description in sorted(matrix_energies.items()):
            data_message += f"\n• Энергия {energy}: {description}"
    
    if additional_count > 0:
        data_message += f"\n\n📊 **Дополнительные данные для сравнения:** {additional_count} человек"
    
    data_message += f"""

**💬 Теперь просто пишите запросы:**
• "Дай мне прогноз на год"
• "Расскажи про мою матрицу"
• "Нужны практики для уверенности"
• "Помоги с отношениями"
• "Сравни меня с [Имя] [Дата]" - для совместимости

Я буду использовать ваши сохраненные данные для всех анализов!"""
    
    sent_message = await message.answer(
        data_message,
        reply_markup=data_management_keyboard,
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
