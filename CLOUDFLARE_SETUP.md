# 🚀 Настройка Cloudflare для деплоя бота

## 1. Установка Wrangler CLI

```bash
npm install -g wrangler
```

## 2. Авторизация в Cloudflare

```bash
wrangler login
```

## 3. Создание KV Storage

```bash
# Создать KV namespace для данных пользователей
wrangler kv:namespace create "USER_DATA"

# Создать preview namespace
wrangler kv:namespace create "USER_DATA" --preview
```

## 4. Создание R2 Storage

```bash
# Создать R2 bucket для файлов
wrangler r2 bucket create telegram-bot-files
```

## 5. Настройка секретов

```bash
# Установить секреты
wrangler secret put TELEGRAM_BOT_TOKEN
wrangler secret put DATABASE_URL
wrangler secret put OPENAI_API_KEY
wrangler secret put OPENAI_ASSISTANT_ID
```

## 6. Обновление wrangler.toml

После создания KV и R2, обновите `wrangler.toml` с правильными ID:

```toml
[[kv_namespaces]]
binding = "USER_DATA"
id = "your-actual-kv-id"
preview_id = "your-actual-preview-kv-id"

[[r2_buckets]]
binding = "FILES"
bucket_name = "telegram-bot-files"
```

## 7. Деплой

```bash
# Деплой в production
wrangler deploy

# Локальная разработка
wrangler dev
```

## 8. Настройка Webhook

После деплоя получите URL вашего Worker и установите webhook:

```bash
# Получить URL
wrangler whoami

# Установить webhook (замените YOUR_BOT_TOKEN и YOUR_WORKER_URL)
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://YOUR_WORKER_URL.workers.dev/webhook"}'
```

## 9. Проверка

```bash
# Проверить логи
wrangler tail

# Проверить статус
wrangler whoami
```

## 10. Мониторинг

- Заходите в [Cloudflare Dashboard](https://dash.cloudflare.com)
- Выберите ваш Worker
- Смотрите логи и метрики в разделе "Analytics"
