from __future__ import annotations

import enum


class Mode(enum.Enum):
    personal = "personal"
    chat = "chat"
    marketing = "marketing"
    sales = "sales"


def prefix_with_mode(message: str, mode: Mode | None) -> str:
    if not mode or mode in (Mode.personal, Mode.chat):
        return message
    return f"[MODE: {mode.value}]\n" + message


MARKETING_WELCOME = (
    "📣 Режим Маркетинг активирован.\n\n"
    "Что могу: идеи постов/рилс, прогревы, шапка профиля, контент‑план, анализ ЦА, чек‑листы качества.\n\n"
    "Примеры запросов:\n"
    "• Сгенерируй 10 идей рилс для [ниша], ЦА [кто], цель [лиды] \n"
    "• Напиши продающий пост для [продукт] с CTA \n"
    "• Контент‑план на неделю для TG+IG"
)


SALES_WELCOME = (
    "💼 Режим Продажи активирован.\n\n"
    "Что могу: воронки, сценарии диагностики, ответы на возражения, офферы, тексты для переписок/вебинаров.\n\n"
    "Примеры запросов:\n"
    "• Скрипт ответа на возражение 'дорого' для консультации по [теме] \n"
    "• Воронка быстрых консультаций на 7 дней \n"
    "• Сценарий диагностической сессии на 30 минут"
)


