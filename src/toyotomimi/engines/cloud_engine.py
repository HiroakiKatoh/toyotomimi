"""クラウドエンジン: AssemblyAI。

`speaker_labels=True` を指定するだけで話者分離つき文字起こしが
1 API で完結する。日本語を含む多言語に対応。
"""

from __future__ import annotations

from ..models import SpeakerSegment, TranscriptResult
from .base import EngineError, ProgressCallback, TranscriptionEngine


class CloudEngine(TranscriptionEngine):
    name = "AssemblyAI (クラウド)"

    def __init__(self, api_key: str, language: str = "ja") -> None:
        if not api_key:
            raise EngineError(
                "AssemblyAI の API キーが設定されていません。設定画面で入力してください。"
            )
        self.api_key = api_key
        self.language = language

    def transcribe(
        self,
        audio_path: str,
        progress: ProgressCallback | None = None,
    ) -> TranscriptResult:
        try:
            import assemblyai as aai
        except ImportError as exc:  # pragma: no cover
            raise EngineError(
                "assemblyai がインストールされていません。`uv sync --extra cloud` を実行してください。"
            ) from exc

        self._report(progress, -1.0, "AssemblyAI にアップロードして解析中...")

        aai.settings.api_key = self.api_key

        config_kwargs: dict = {"speaker_labels": True}
        if self.language and self.language != "auto":
            config_kwargs["language_code"] = self.language
        else:
            config_kwargs["language_detection"] = True

        config = aai.TranscriptionConfig(**config_kwargs)

        try:
            transcript = aai.Transcriber().transcribe(audio_path, config)
        except Exception as exc:
            raise EngineError(f"AssemblyAI の呼び出しに失敗しました: {exc}") from exc

        if transcript.status == aai.TranscriptStatus.error:
            raise EngineError(f"解析に失敗しました: {transcript.error}")

        self._report(progress, 0.9, "結果を整形中...")

        segments: list[SpeakerSegment] = []
        for utt in transcript.utterances or []:
            segments.append(
                SpeakerSegment(
                    speaker=f"話者{utt.speaker}",  # "A" -> "話者A"
                    start=(utt.start or 0) / 1000.0,  # ms -> 秒
                    end=(utt.end or 0) / 1000.0,
                    text=(utt.text or "").strip(),
                )
            )

        detected_lang = (
            self.language
            if self.language and self.language != "auto"
            else getattr(transcript, "language_code", None)
        )

        self._report(progress, 1.0, "完了")
        return TranscriptResult(
            segments=segments,
            language=detected_lang,
            engine=self.name,
            audio_path=audio_path,
        )
