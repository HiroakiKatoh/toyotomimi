"""解析結果の出力。txt / SRT / JSON に対応。"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import TranscriptResult


def to_text(result: TranscriptResult) -> str:
    """話者ラベル付きのプレーンテキスト。"""
    lines = [f"# 文字起こし結果 (エンジン: {result.engine}, 言語: {result.language})", ""]
    for seg in result.segments:
        lines.append(f"{seg.speaker}: {seg.text}")
    return "\n".join(lines)


def to_srt(result: TranscriptResult) -> str:
    """SRT 字幕形式(話者名を本文先頭に付与)。"""
    blocks = []
    for i, seg in enumerate(result.segments, start=1):
        blocks.append(
            f"{i}\n"
            f"{_srt_time(seg.start)} --> {_srt_time(seg.end)}\n"
            f"{seg.speaker}: {seg.text}\n"
        )
    return "\n".join(blocks)


def to_json(result: TranscriptResult) -> str:
    """構造化 JSON。"""
    payload = {
        "engine": result.engine,
        "language": result.language,
        "audio_path": result.audio_path,
        "speakers": result.speakers,
        "segments": [asdict(seg) for seg in result.segments],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def save(result: TranscriptResult, path: str) -> None:
    """拡張子に応じて出力形式を自動選択して保存する。"""
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".srt":
        content = to_srt(result)
    elif ext == ".json":
        content = to_json(result)
    else:
        content = to_text(result)
    p.write_text(content, encoding="utf-8")


def _srt_time(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
