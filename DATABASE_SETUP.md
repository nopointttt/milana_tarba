# 🗄️ Настройка базы данных

Инструкция по настройке подключения к Neon PostgreSQL для бота "Аналитик".

## 📋 Предварительные требования

1. **Аккаунт Neon** - [neon.tech](https://neon.tech)
2. **Python 3.11+** с установленными зависимостями
3. **PostgreSQL клиент** (опционально, для прямого подключения)

## 🚀 Быстрый старт

### 1. Создание базы данных в Neon

1. Зайдите в [Neon Console](https://console.neon.tech)
2. Создайте новый проект или используйте существующий
3. Скопируйте **Connection String** из раздела "Connection Details"
4. Формат должен быть: `postgresql://username:password@host/database`

### 2. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```bash
# Скопируйте из env.example
cp env.example .env
```

Отредактируйте `.env`:

```env
# Обязательные параметры
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql+psycopg://username:password@host:port/database

# Остальные параметры...
```

**Важно:** URL должен начинаться с `postgresql+psycopg://` для асинхронной работы!

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Инициализация миграций

```bash
python init_migrations.py
```

### 5. Создание первой миграции

```bash
alembic revision --autogenerate -m "Initial migration"
```

### 6. Применение миграций

```bash
alembic upgrade head
```

### 7. Тестирование подключения

```bash
python test_database.py
```

## 🔧 Команды для работы с миграциями

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Описание изменений"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Показать текущую версию
alembic current

# Показать историю миграций
alembic history
```

## 🧪 Тестирование

### Автоматический тест

```bash
python test_database.py
```

### Ручное тестирование

1. Запустите бота: `python main.py`
2. Отправьте `/start` в Telegram
3. Введите дату рождения и имя
4. Проверьте, что анализ сохранился в БД

## 📊 Структура базы данных

### Таблицы

- **users** - пользователи Telegram
- **dialogs** - диалоги с ботом
- **messages** - сообщения в диалогах
- **report_requests** - запросы на анализ
- **name_transliterations** - транслитерации имён

### Основные поля

```sql
-- Пользователи
users: id, telegram_user_id, username, full_name, created_at, updated_at

-- Запросы анализов
report_requests: id, user_id, full_name, birth_date, status, result_text, error, created_at, updated_at
```

## 🚨 Устранение неполадок

### Ошибка подключения

```
RuntimeError: DATABASE_URL не задан в окружении
```

**Решение:** Проверьте файл `.env` и переменную `DATABASE_URL`

### Ошибка миграций

```
sqlalchemy.exc.ProgrammingError: relation "users" does not exist
```

**Решение:** Примените миграции: `alembic upgrade head`

### Ошибка асинхронности

```
TypeError: 'coroutine' object is not iterable
```

**Решение:** Убедитесь, что используете `postgresql+psycopg://` в URL

## 🔒 Безопасность

1. **Никогда не коммитьте** файл `.env` в Git
2. **Используйте** переменные окружения в продакшене
3. **Ограничьте доступ** к базе данных по IP
4. **Регулярно обновляйте** пароли

## 📈 Мониторинг

### Логи

Бот логирует все операции с БД в консоль (в development режиме).

### Метрики

- Количество пользователей
- Количество выполненных анализов
- Время выполнения запросов
- Ошибки подключения

## 🆘 Поддержка

При возникновении проблем:

1. Проверьте логи бота
2. Запустите `python test_database.py`
3. Проверьте статус Neon в [статус-странице](https://status.neon.tech)
4. Обратитесь к [документации Neon](https://neon.tech/docs)
