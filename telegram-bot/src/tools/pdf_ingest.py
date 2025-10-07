"""Utility to convert PDF to UTF-8 TXT and place it into media/extra_knowledge.

Usage (non-interactive):
  python -m src.tools.pdf_ingest "C:/path/to/file.pdf"

This script will:
  - read the PDF,
  - extract text page by page with PyPDF2,
  - write a .txt file named after the PDF into project_root/media/extra_knowledge.

Requirements: PyPDF2
"""
from __future__ import annotations

import sys
from pathlib import Path
import argparse


def ensure_output_dir(project_root: Path) -> Path:
    media_dir = project_root / "media"
    extra_dir = media_dir / "extra_knowledge"
    extra_dir.mkdir(parents=True, exist_ok=True)
    return extra_dir


def extract_pdf_text(pdf_path: Path) -> str:
    try:
        from PyPDF2 import PdfReader
    except Exception as e:
        raise RuntimeError("PyPDF2 не установлен. Добавьте его в requirements и установите зависимости.") from e

    reader = PdfReader(str(pdf_path))
    chunks = []
    for page in reader.pages:
        text = page.extract_text() or ""
        chunks.append(text)
    return "\n\n".join(chunks)


def convert_pdf_to_txt(input_pdf: Path, output_dir: Path) -> Path:
    text = extract_pdf_text(input_pdf)
    safe_name = input_pdf.stem.strip() or "document"
    output_path = output_dir / f"{safe_name}.txt"
    output_path.write_text(text, encoding="utf-8")
    return output_path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Convert PDF to TXT for extra knowledge ingestion")
    parser.add_argument("pdf_path", help="Absolute path to PDF file")
    args = parser.parse_args(argv)

    input_pdf = Path(args.pdf_path)
    if not input_pdf.exists():
        print(f"Файл не найден: {input_pdf}")
        return 1

    # project root is 3 levels up from this file (telegram-bot/src/tools)
    project_root = Path(__file__).parent.parent.parent.parent
    output_dir = ensure_output_dir(project_root)
    output_txt = convert_pdf_to_txt(input_pdf, output_dir)
    print(f"Готово: {output_txt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


