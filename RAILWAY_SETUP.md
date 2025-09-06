# 🚀 Настройка Railway для деплоя бота

## 1. Создание аккаунта Railway

1. Зайдите на [railway.app](https://railway.app)
2. Войдите через GitHub
3. Подтвердите email

## 2. Подготовка проекта

Убедитесь, что у вас есть файлы:
- ✅ `main.py` - основной файл бота
- ✅ `requirements.txt` - зависимости Python
- ✅ `railway.json` - конфигурация Railway
- ✅ `Procfile` - команда запуска

## 3. Деплой через Railway Dashboard

### Шаг 1: Создание проекта
1. Нажмите "New Project"
2. Выберите "Deploy from GitHub repo"
3. Выберите ваш репозиторий

### Шаг 2: Настройка переменных окружения
В разделе "Variables" добавьте:
```
TELEGRAM_BOT_TOKEN=your_bot_token
DATABASE_URL=your_neon_database_url
OPENAI_API_KEY=your_openai_key
OPENAI_ASSISTANT_ID=your_assistant_id
```

### Шаг 3: Деплой
1. Railway автоматически определит Python проект
2. Установит зависимости из `requirements.txt`
3. Запустит бота командой из `Procfile`

## 4. Настройка Webhook

После деплоя получите URL вашего бота:
1. В Railway Dashboard найдите "Public URL"
2. Скопируйте URL (например: `https://your-app.railway.app`)

### Установка Webhook через Telegram API:
```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-app.railway.app/webhook"}'
```

## 5. Проверка работы

1. Отправьте `/start` боту в Telegram
2. Проверьте логи в Railway Dashboard
3. Убедитесь, что бот отвечает

## 6. Мониторинг

- **Логи**: Railway Dashboard → ваш проект → "Deployments" → "View Logs"
- **Метрики**: Railway Dashboard → ваш проект → "Metrics"
- **Переменные**: Railway Dashboard → ваш проект → "Variables"

## 7. Обновление бота

При каждом push в GitHub Railway автоматически:
1. Пересоберет проект
2. Перезапустит бота
3. Применит новые изменения

## 8. Troubleshooting

### Проблема: Бот не отвечает
- Проверьте логи в Railway Dashboard
- Убедитесь, что webhook установлен правильно
- Проверьте переменные окружения

### Проблема: Ошибки базы данных
- Проверьте `DATABASE_URL` в переменных окружения
- Убедитесь, что Neon PostgreSQL доступен

### Проблема: OpenAI не работает
- Проверьте `OPENAI_API_KEY` и `OPENAI_ASSISTANT_ID`
- Убедитесь, что у вас есть кредиты на OpenAI
