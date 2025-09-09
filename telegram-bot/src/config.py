"""src/config.py
Конфигурация приложения. Все секреты читаются из окружения/секрет-хранилища Cloudflare.
Не храните токены и ключи в коде.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Settings:
    """Настройки приложения.

    Источник правды для секретов — зашифрованное хранилище секретов Cloudflare.
    На локальной машине используйте переменные окружения.
    """

    telegram_bot_token: str
    openai_api_key: str
    database_url: str

    # Необязательные интеграции/параметры
    sentry_dsn: Optional[str] = None
    environment: str = "development"  # development|staging|production
    openai_assistant_id: Optional[str] = None  # ID ассистента OpenAI

    # Cloudflare/Infra
    cf_account_id: Optional[str] = None
    kv_namespace: Optional[str] = None
    r2_bucket: Optional[str] = None

    # Контроль расходов
    rate_limit_per_minute: int = 30

    @classmethod
    def from_env(cls) -> "Settings":
        """Собрать настройки из переменных окружения.

        Обязательные: TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, DATABASE_URL
        """
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        openai_api_key = os.getenv("OPENAI_API_KEY", "")
        database_url = os.getenv("DATABASE_URL", "")

        if not telegram_bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN не задан в окружении")
        if not openai_api_key:
            raise RuntimeError("OPENAI_API_KEY не задан в окружении")
        if not database_url:
            raise RuntimeError("DATABASE_URL не задан в окружении")

        return cls(
            telegram_bot_token=telegram_bot_token,
            openai_api_key=openai_api_key,
            database_url=database_url,
            sentry_dsn=os.getenv("SENTRY_DSN"),
            environment=os.getenv("ENVIRONMENT", "development"),
            openai_assistant_id=os.getenv("OPENAI_ASSISTANT_ID"),
            cf_account_id=os.getenv("CF_ACCOUNT_ID"),
            kv_namespace=os.getenv("CF_KV_NAMESPACE"),
            r2_bucket=os.getenv("CF_R2_BUCKET"),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "30")),
        )
