"""音声前処理ユーティリティ。

pyannote は MP3/M4A など一部の形式を直接読めないため、解析前に
16kHz / モノラルの WAV へ正規化する。変換には ffmpeg を用いる。
"""

from __future__ import annotations

import array
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path


class FfmpegNotFoundError(RuntimeError):
    """ffmpeg が見つからない場合に送出。"""


def _resolve_ffmpeg() -> str | None:
    """ffmpeg 実行ファイルのパスを返す。見つからなければ None。"""
    override = os.environ.get("FFMPEG_PATH", "").strip()
    if override and Path(override).is_file():
        return override

    found = shutil.which("ffmpeg")
    if found:
        return found

    if sys.platform == "win32":
        winget_root = (
            Path(os.environ.get("LOCALAPPDATA", ""))
            / "Microsoft/WinGet/Packages"
        )
        if winget_root.is_dir():
            for candidate in winget_root.glob("Gyan.FFmpeg*/**/bin/ffmpeg.exe"):
                if candidate.is_file():
                    return str(candidate)

    return None


def ffmpeg_available() -> bool:
    return _resolve_ffmpeg() is not None


def to_wav_16k_mono(audio_path: str, out_path: str | None = None) -> str:
    """音声を 16kHz / モノラル / 16bit PCM WAV へ変換し、そのパスを返す。

    `out_path` を省略すると一時ファイルを生成する(呼び出し側で削除すること)。
    """
    ffmpeg = _resolve_ffmpeg()
    if not ffmpeg:
        raise FfmpegNotFoundError(
            "ffmpeg が見つかりません。インストールして PATH を通してください。"
        )

    src = Path(audio_path)
    if not src.exists():
        raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_path}")

    if out_path is None:
        fd, tmp = tempfile.mkstemp(suffix=".wav", prefix="toyotomimi_")
        os.close(fd)
        out_path = tmp

    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(src),
        "-ar",
        "16000",
        "-ac",
        "1",
        "-c:a",
        "pcm_s16le",
        out_path,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg による変換に失敗しました:\n{proc.stderr.strip()}")
    return out_path


def load_wav_tensor(wav_path: str):
    """16bit PCM WAV を (channel, time) の float32 テンソルとして読み込む。"""
    import torch

    with wave.open(wav_path, "rb") as wf:
        if wf.getsampwidth() != 2:
            raise ValueError("16bit PCM WAV のみ対応しています。")
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        frames = wf.readframes(wf.getnframes())

    samples = array.array("h")
    samples.frombytes(frames)
    waveform = torch.tensor(samples, dtype=torch.float32) / 32768.0

    if n_channels == 1:
        return waveform.unsqueeze(0), sample_rate

    waveform = waveform.reshape(-1, n_channels).T
    return waveform.mean(dim=0, keepdim=True), sample_rate
