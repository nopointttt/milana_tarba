"""Resume transcription for already converted audios/chunks in media/transcriptions.

- Scans media/transcriptions/* subfolders
- If <video>.txt missing, tries to transcribe existing chunks/*.m4a
  - If chunks missing but <video>.m4a exists, splits it into chunks (2600s)
  - Uses 24 MB per-file size guard
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List
from tqdm import tqdm
import subprocess


def run_ffmpeg(ffmpeg_bin: str, args: List[str]) -> None:
    cmd = [ffmpeg_bin, *args]
    subprocess.run(cmd, check=True)


def split_audio(ffmpeg_bin: str, input_audio: Path, out_dir: Path, segment_seconds: int = 2600) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / f"{input_audio.stem}_%03d.m4a"
    run_ffmpeg(
        ffmpeg_bin,
        [
            "-y", "-i", str(input_audio),
            "-c", "copy", "-f", "segment", "-segment_time", str(segment_seconds),
            "-reset_timestamps", "1",
            str(pattern),
        ],
    )
    return sorted(out_dir.glob(f"{input_audio.stem}_*.m4a"))


def transcribe_chunks_openai(chunks: List[Path]) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY не задан в окружении")
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    limit_bytes = 24 * 1024 * 1024
    texts: List[str] = []
    for ch in tqdm(chunks, desc="Чанки", unit="часть"):
        if ch.stat().st_size > limit_bytes:
            raise RuntimeError(f"Chunk exceeds 24MB limit: {ch.name}")
        with open(ch, "rb") as f:
            r = client.audio.transcriptions.create(model="whisper-1", file=f)
            texts.append(r.text.strip() if hasattr(r, "text") else str(r))
    return "\n\n".join(texts)


def main() -> int:
    project_root = Path(__file__).parent.parent.parent.parent
    trans_root = project_root / "media" / "transcriptions"
    ffmpeg = str(project_root / "video_transcription" / "ffmpeg-master-latest-win64-gpl" / "bin" / "ffmpeg.exe")
    if not Path(ffmpeg).exists():
        ffmpeg = "ffmpeg"

    if not trans_root.exists():
        print("Папка media/transcriptions не найдена")
        return 1

    subfolders = [p for p in trans_root.iterdir() if p.is_dir()]
    if not subfolders:
        print("Нет папок для возобновления")
        return 0

    ok, fail = 0, 0
    for folder in tqdm(subfolders, desc="Папки", unit="видео"):
        # Expected base filename equals folder name
        base = folder.name
        txt_path = folder / f"{base}.txt"
        if txt_path.exists() and txt_path.stat().st_size > 0:
            continue
        m4a_path = folder / f"{base}.m4a"
        chunks_dir = folder / "chunks"
        chunks = sorted(chunks_dir.glob("*.m4a")) if chunks_dir.exists() else []
        try:
            if not chunks:
                if not m4a_path.exists():
                    print(f"Пропущено (нет m4a и чанков): {folder}")
                    fail += 1
                    continue
                chunks = split_audio(ffmpeg, m4a_path, chunks_dir, segment_seconds=2600)
            transcript = transcribe_chunks_openai(chunks)
            txt_path.write_text(transcript, encoding="utf-8")
            print(f"OK: {folder.name} -> {txt_path}")
            ok += 1
        except Exception as e:
            print(f"FAIL: {folder.name} -> {e}")
            fail += 1

    print(f"Готово. Успешно: {ok}, ошибок: {fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())


