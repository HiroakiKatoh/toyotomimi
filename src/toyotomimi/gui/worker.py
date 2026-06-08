"""バックグラウンドで解析を実行する QThread ワーカー。

解析は重く時間がかかるため、UI スレッドをブロックしないよう別スレッドで
実行し、進捗・完了・エラーをシグナルで通知する。
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from ..config import AppConfig
from ..engines import EngineError, build_engine
from ..models import TranscriptResult


class TranscribeWorker(QThread):
    progress = Signal(float, str)  # (0.0-1.0 または負値=不定, メッセージ)
    finished_ok = Signal(object)  # TranscriptResult
    failed = Signal(str)

    def __init__(self, audio_path: str, config: AppConfig) -> None:
        super().__init__()
        self._audio_path = audio_path
        self._config = config

    def run(self) -> None:  # QThread のエントリポイント
        try:
            engine = build_engine(self._config)
            result: TranscriptResult = engine.transcribe(
                self._audio_path,
                progress=lambda r, m: self.progress.emit(r, m),
            )
            self.finished_ok.emit(result)
        except EngineError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # 想定外のエラーも UI に表示
            self.failed.emit(f"予期せぬエラー: {exc}")
