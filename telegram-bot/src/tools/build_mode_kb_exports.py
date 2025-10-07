"""Build two consolidated TXT knowledge files for Marketing and Sales modes.

Sources:
- media/extra_knowledge/*.txt (PDF + transcripts already ingested)

Routing heuristics (by filename/title):
- Sales: продажи, воронки, вебинар, диагностическ, продажам, сессии, найм, менеджмент, команда (org), оффер
- Marketing: упаковка, контент, прогрев, блог, Telegram, стратегия, аудитория, идея, продукт, визуал, хайлайтс, рилс

Outputs:
- media/openai_exports/marketing_kb.txt
- media/openai_exports/sales_kb.txt
"""
from __future__ import annotations

from pathlib import Path
import re


SALES_KEYWORDS = [
    "продажи", "воронки", "вебинар", "диагностическ", "продажам", "сессии",
    "найм", "менеджмент", "команда", "оффер",
]

MARKETING_KEYWORDS = [
    "упаковка", "контент", "прогрев", "блог", "telegram", "стратегия", "аудитория",
    "идея", "продукт", "визуал", "хайлайтс", "рилс",
]


def classify_mode(name: str, sample_text: str) -> str:
    text = f"{name}\n{sample_text}".lower()
    # Simple score by keyword presence
    sales_score = sum(1 for k in SALES_KEYWORDS if k in text)
    marketing_score = sum(1 for k in MARKETING_KEYWORDS if k in text)
    if sales_score > marketing_score:
        return "sales"
    if marketing_score > sales_score:
        return "marketing"
    # Fallback by common terms
    if "продаж" in text or "воронк" in text:
        return "sales"
    return "marketing"


def main() -> int:
    project_root = Path(__file__).parent.parent.parent.parent
    extra = project_root / "media" / "extra_knowledge"
    export = project_root / "media" / "openai_exports"
    export.mkdir(parents=True, exist_ok=True)

    marketing_parts = []
    sales_parts = []

    files = sorted(p for p in extra.glob("*.txt"))
    if not files:
        print("Нет файлов в media/extra_knowledge")
        return 1

    for fp in files:
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # Sample first 2k chars for classification
        sample = content[:2000]
        mode = classify_mode(fp.stem, sample)
        header = f"===== SOURCE: {fp.name} | MODE: {mode.upper()} =====\n"
        block = header + content.strip() + "\n\n"
        if mode == "sales":
            sales_parts.append(block)
        else:
            marketing_parts.append(block)

    marketing_out = export / "marketing_kb.txt"
    sales_out = export / "sales_kb.txt"
    marketing_out.write_text("\n".join(marketing_parts), encoding="utf-8")
    sales_out.write_text("\n".join(sales_parts), encoding="utf-8")

    print(f"OK: {marketing_out}")
    print(f"OK: {sales_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


