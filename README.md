# AI-ассистент «Аналитик» (MVP)

Телеграм-бот по цифровой психологии (система Миланы Тарба). Модуль «Аналитик» рассчитывает ключевые показатели (ЧС, ЧД, Матрица, Число Имени) и формирует структурированный отчёт, опираясь на правила «Книги Знаний».

## Техстек
- Python 3.11+, Aiogram 3.x
- Serverless: Cloudflare Workers, KV, Queues, R2
- БД: Neon (PostgreSQL)
- ORM: SQLModel + Alembic
- AI: OpenAI API (GPT-4.1)
- Мониторинг: Sentry

## Структура каталогов
- `src/handlers/` — роутеры Aiogram (например, `start.py`)
- `src/middlewares/` — DI-мидлвары (`di.py`)
- `src/services/` — сервисы и интеграции (`openai_client.py`)
- `src/db/` — `models.py`, `base.py` (engine/session)
- `src/config.py` — конфигурация из окружения/секретов
- `main.py` — локальная точка входа (polling). В production — webhook.

## Конфигурация окружения
Создайте файл `.env` на основе `.env.example` и задайте переменные:
- `TELEGRAM_BOT_TOKEN`
- `OPENAI_API_KEY`
- `DATABASE_URL` (например, `postgresql+psycopg://USER:PASSWORD@HOST/DB`)
- `SENTRY_DSN` (опционально)
- `ENVIRONMENT` (`development|staging|production`)
- `CF_ACCOUNT_ID`, `CF_KV_NAMESPACE`, `CF_R2_BUCKET` (при необходимости)
- `RATE_LIMIT_PER_MINUTE` (по умолчанию 30)

Секреты не хранятся в репозитории — в продакшене используйте зашифрованные секреты Cloudflare.

## Локальный запуск (dev)
1) Python 3.11+
2) Установите зависимости (будет формализовано в Phase 1 через requirements/poetry):
   - aiogram, sqlmodel, psycopg[binary], sentry-sdk
3) Экспортируйте переменные окружения или используйте `.env`.
4) Запустите:
```bash
python main.py
```

В продакшене используется webhook на Cloudflare Workers (см. `ARCHITECTURE.md`).

## Качество кода
- Форматирование: `black`
- Линтер: `ruff`
- Тесты: `pytest` (юнит-тесты для ключевой математики из «Книги Знаний»)

## Безопасность и приватность
- Все секреты — через Cloudflare Secrets
- История диалогов хранится в Neon; реализуются механизмы удаления по запросу
- Логи и ошибки — Sentry

## Состояние проекта
- Фаза 0 (Архитектура) — завершена, см. `ARCHITECTURE.md`
- Фаза 1 — см. `BACKLOG.md` (модуль «Аналитик»)
