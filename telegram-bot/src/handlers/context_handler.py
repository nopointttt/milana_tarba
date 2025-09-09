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
    
    # Проверяем, есть ли уже данные пользователя
    if user_id in user_data:
        # Показываем закрепленное сообщение с данными
        await show_user_data_message(message)
    else:
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
    
    if len(lines) == 2:
        name, date = lines[0], lines[1]
        # Если имя или дата отличаются от основных данных пользователя
        if (is_name_format(name) and is_date_format(date) and 
            (name != user_main_data.get('name') or date != user_main_data.get('birth_date'))):
            return True
    
    return False

def extract_additional_data(message_text: str) -> Dict[str, str]:
    """Извлекает дополнительные данные из сообщения."""
    lines = [line.strip() for line in message_text.strip().split('\n') if line.strip()]
    if len(lines) == 2:
        return {
            'name': lines[0],
            'birth_date': lines[1]
        }
    return {}

def clear_additional_data(user_id: int) -> None:
    """Очищает дополнительные данные пользователя."""
    if user_id in additional_data:
        additional_data[user_id] = []

async def handle_data_input(message: types.Message) -> bool:
    """Обработка ввода данных пользователем. Возвращает True если данные обработаны."""
    user_id = message.from_user.id
    user_message = message.text.strip()
    
    # Если у пользователя уже есть данные, не обрабатываем как ввод данных
    if user_id in user_data:
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
    """Проверяет, является ли текст датой."""
    import re
    date_patterns = [
        r'\d{1,2}\.\d{1,2}\.\d{4}',
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{1,2}-\d{1,2}-\d{4}',
        r'\d{1,2}\s+\d{1,2}\s+\d{4}'
    ]
    
    for pattern in date_patterns:
        if re.match(pattern, text):
            return True
    return False


def is_name_format(text: str) -> bool:
    """Проверяет, является ли текст именем."""
    # Простая проверка: только буквы, одно слово, длина 2-20 символов
    if not text or not text.strip():
        return False
    
    text = text.strip()
    
    # Проверяем, что это одно слово (нет пробелов)
    if ' ' in text:
        return False
    
    # Проверяем, что все символы - буквы
    if not text.isalpha():
        return False
    
    # Проверяем длину
    if len(text) < 2 or len(text) > 20:
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
    
    # Сохраняем данные
    user_data[user_id] = {
        "name": name,
        "birth_date": birth_date
    }
    
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
                enhanced_message = f"Пользователь: {user_message}\n\nОсновные данные пользователя:\nИмя: {user_data_info['name']}\nДата рождения: {user_data_info['birth_date']}\n\nДополнительные данные для сравнения:\nИмя: {additional_info['name']}\nДата рождения: {additional_info['birth_date']}"
            else:
                # Обычное сообщение с основными данными
                user_data_info = user_data[user_id]
                enhanced_message = f"Пользователь: {user_message}\n\nДанные пользователя:\nИмя: {user_data_info['name']}\nДата рождения: {user_data_info['birth_date']}"
            
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
    
    # Удаляем предыдущее закрепленное сообщение, если есть
    if user_id in pinned_messages:
        try:
            await callback_query.bot.delete_message(
                chat_id=callback_query.message.chat.id,
                message_id=pinned_messages[user_id]
            )
        except:
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
    
    # Очищаем дополнительные данные при обновлении основных
    clear_additional_data(user_id)
    
    # Удаляем статусное сообщение
    try:
        if status_msg:
            await status_msg.delete()
    except Exception:
        pass
    
    # Перенаправляем на ввод данных
    await handle_input_data(callback_query)


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
    
    data = user_data[user_id]
    name = data.get("name", "Не указано")
    birth_date = data.get("birth_date", "Не указано")
    
    # Проверяем наличие дополнительных данных
    additional_count = len(additional_data.get(user_id, []))
    
    data_message = f"""✅ **Ваши данные сохранены!**

👤 **Имя:** {name}
📅 **Дата рождения:** {birth_date}"""
    
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
