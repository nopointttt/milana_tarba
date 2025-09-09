"""src/services/openai_client.py
Интерфейс клиента OpenAI. Реализация — заглушка для MVP архитектурного спринта.

Важно: Ключи не храним в коде. Ключ читается из окружения/секрета Cloudflare.
"""
from __future__ import annotations

from datetime import date


class OpenAIClient:
    """Обёртка над OpenAI API для задач модуля "Аналитик".

    В последующих фазах реализуем реальные вызовы GPT-4.1.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def analyze_numbers(self, birth_date: date, transliterated_name: str) -> str:
        """Вернуть текст отчёта (заглушка).

        В реальной реализации здесь будет обращение к OpenAI, а также
        строгая привязка к алгоритмам из "Книги Знаний" (см. user rules 1.1).
        """
        return (
            "Ваш персональный анализ находится в разработке. "
            "Как только модуль расчётов будет подключён, вы получите подробный отчёт."
        )
