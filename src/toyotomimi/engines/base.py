"""エンジンの抽象基底。

GUI 側はこのインターフェースだけに依存する。新しいバックエンドを追加する
場合も `TranscriptionEngine` を実装すればよい。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from ..models import TranscriptResult

# (進捗率 0.0-1.0, メッセージ) を受け取るコールバック。進捗率が不明な場合は負値。
ProgressCallback = Callable[[float, str], None]


class EngineError(RuntimeError):
    """エンジン実行時のエラー(設定不足・API失敗など)。"""


class TranscriptionEngine(ABC):
    """話者分離つき文字起こしエンジンの共通インターフェース。"""

    #: UI 表示用の名前
    name: str = "engine"

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        progress: ProgressCallback | None = None,
    ) -> TranscriptResult:
        """音声ファイルを解析し話者分離つきの結果を返す。"""
        raise NotImplementedError

    @staticmethod
    def _report(progress: ProgressCallback | None, ratio: float, message: str) -> None:
        if progress is not None:
            progress(ratio, message)
