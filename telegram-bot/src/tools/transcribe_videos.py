"""Batch video transcription via ffmpeg + OpenAI Whisper API.

Steps per video:
1) Convert to audio (AAC m4a, mono, 16kHz, 64kbps)
2) Split audio into chunks <= ~25MB using fixed duration (default ~3000s at 64kbps)
3) Transcribe each chunk via OpenAI Whisper API
4) Save merged transcript to media/transcriptions/<video_stem>.txt

Usage:
  python -m src.tools.transcribe_videos --input "C:/path/to/folder" [--ffmpeg "C:/path/ffmpeg.exe"]

Requires env var OPENAI_API_KEY to be set.
"""
from __future__ import annotations

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List
from tqdm import tqdm


VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v", ".webm"}


def find_videos(root: Path) -> List[Path]:
    return [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTS]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def run_ffmpeg(ffmpeg_bin: str, args: List[str]) -> None:
    cmd = [ffmpeg_bin, *args]
    # Stream output directly to terminal to observe progress/errors live
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg error (code {e.returncode}) while running: {' '.join(cmd)}") from e


def convert_to_audio(ffmpeg_bin: str, input_video: Path, output_audio: Path) -> None:
    # Mono, 16kHz, 64kbps AAC to keep size small for chunking
    run_ffmpeg(
        ffmpeg_bin,
        [
            "-y", "-i", str(input_video),
            "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k", "-c:a", "aac",
            str(output_audio),
        ],
    )


def split_audio(ffmpeg_bin: str, input_audio: Path, out_dir: Path, segment_seconds: int = 2600) -> List[Path]:
    ensure_dir(out_dir)
    # Segment by time; ~2600s at ~70kbps ≈ < 24MB
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

    # OpenAI Python SDK v2 style
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("OpenAI SDK не установлен") from e

    client = OpenAI(api_key=api_key)
    limit_bytes = 24 * 1024 * 1024
    texts: List[str] = []
    for chunk in tqdm(chunks, desc="Чанки", unit="часть"):
        if chunk.stat().st_size > limit_bytes:
            raise RuntimeError(f"Chunk exceeds 24MB limit: {chunk.name}")
        with open(chunk, "rb") as f:
            result = client.audio.transcriptions.create(model="whisper-1", file=f)
            texts.append(result.text.strip() if hasattr(result, "text") else str(result))
    return "\n\n".join(texts)


def process_video(ffmpeg_bin: str, video_path: Path, transcriptions_root: Path) -> Path:
    output_dir = transcriptions_root / video_path.stem
    ensure_dir(output_dir)

    audio_path = output_dir / f"{video_path.stem}.m4a"
    convert_to_audio(ffmpeg_bin, video_path, audio_path)

    chunks_dir = output_dir / "chunks"
    chunks = split_audio(ffmpeg_bin, audio_path, chunks_dir)
    if not chunks:
        # If splitting produced nothing, fallback to original audio
        chunks = [audio_path]

    transcript = transcribe_chunks_openai(chunks)
    out_txt = output_dir / f"{video_path.stem}.txt"
    out_txt.write_text(transcript, encoding="utf-8")
    return out_txt


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Batch transcribe videos via ffmpeg + OpenAI Whisper")
    parser.add_argument("--input", required=True, help="Folder with videos (recursively)")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="Path to ffmpeg executable (default: ffmpeg in PATH)")
    parser.add_argument("--segment-seconds", type=int, default=3000, help="Segment duration in seconds")
    args = parser.parse_args(argv)

    input_root = Path(args.input)
    if not input_root.exists():
        print(f"Папка не найдена: {input_root}")
        return 1

    # Resolve project root: telegram-bot/src/tools -> project root is 3 levels up
    project_root = Path(__file__).parent.parent.parent.parent
    transcriptions_root = project_root / "media" / "transcriptions"
    ensure_dir(transcriptions_root)

    videos = find_videos(input_root)
    if not videos:
        print("Видео не найдены.")
        return 0

    print(f"Найдено видео файлов: {len(videos)}")
    ok, fail = 0, 0
    for vp in tqdm(videos, desc="Обработка видео", unit="файл"):
        try:
            out_txt = process_video(args.ffmpeg, vp, transcriptions_root)
            tqdm.write(f"OK: {vp.name} -> {out_txt}")
            ok += 1
        except Exception as e:
            tqdm.write(f"FAIL: {vp} -> {e}")
            fail += 1

    print(f"Готово. Успешно: {ok}, ошибок: {fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


