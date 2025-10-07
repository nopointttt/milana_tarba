"""Collect all transcript .txt files and copy into media/extra_knowledge for RAG.

Rules:
- Source: media/transcriptions/*/<video>.txt
- Target: media/extra_knowledge/<folder_name>.txt (keep Unicode names)
- Overwrite existing targets
"""
from __future__ import annotations

from pathlib import Path
import shutil


def main() -> int:
    project_root = Path(__file__).parent.parent.parent.parent
    trans_root = project_root / "media" / "transcriptions"
    extra_dir = project_root / "media" / "extra_knowledge"
    extra_dir.mkdir(parents=True, exist_ok=True)

    if not trans_root.exists():
        print("Папка media/transcriptions не найдена")
        return 1

    total, copied = 0, 0
    for folder in sorted(p for p in trans_root.iterdir() if p.is_dir()):
        base = folder.name
        src = folder / f"{base}.txt"
        if not src.exists():
            continue
        total += 1
        dst = extra_dir / f"{base}.txt"
        shutil.copyfile(src, dst)
        copied += 1
        print(f"OK: {src.name} -> extra_knowledge/{dst.name}")

    print(f"Готово. Найдено: {total}, скопировано: {copied}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


