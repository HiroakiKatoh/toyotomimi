"""ローカルエンジン: faster-whisper + pyannote.audio。

処理の流れ:
  1. ffmpeg で 16kHz/モノラル WAV に変換
  2. pyannote で話者区間(誰がいつ話したか)を取得
  3. faster-whisper でセグメント単位の文字起こし
  4. 各文字起こしセグメントを、時間的に最も重なる話者区間へ割り当て
"""

from __future__ import annotations

import os
import tempfile

from ..audio import load_wav_tensor, to_wav_16k_mono
from ..models import SpeakerSegment, TranscriptResult
from .base import EngineError, ProgressCallback, TranscriptionEngine

_DIARIZATION_MODEL = "pyannote/speaker-diarization-3.1"


class LocalEngine(TranscriptionEngine):
    name = "faster-whisper + pyannote (ローカル)"

    def __init__(
        self,
        hf_token: str,
        model_size: str = "small",
        language: str = "ja",
    ) -> None:
        if not hf_token:
            raise EngineError(
                "Hugging Face トークンが設定されていません。設定画面で入力してください。"
            )
        self.hf_token = hf_token
        self.model_size = model_size
        self.language = language

    def transcribe(
        self,
        audio_path: str,
        progress: ProgressCallback | None = None,
    ) -> TranscriptResult:
        try:
            import torch
            from faster_whisper import WhisperModel
            from pyannote.audio import Pipeline
        except ImportError as exc:  # pragma: no cover
            raise EngineError(
                "ローカル処理の依存が未インストールです。`uv sync --extra local` を実行してください。"
            ) from exc

        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        # 1. 音声を正規化
        self._report(progress, -1.0, "音声を変換中...")
        wav_path = to_wav_16k_mono(audio_path)

        try:
            # 2. 話者分離
            self._report(progress, -1.0, "話者分離モデルを読み込み中...")
            try:
                pipeline = Pipeline.from_pretrained(
                    _DIARIZATION_MODEL, token=self.hf_token
                )
            except Exception as exc:
                raise EngineError(
                    "話者分離モデルの読み込みに失敗しました。HF トークンと "
                    f"{_DIARIZATION_MODEL} の利用規約同意を確認してください: {exc}"
                ) from exc
            pipeline.to(torch.device(device))

            self._report(progress, -1.0, "話者を分析中...")
            waveform, sample_rate = load_wav_tensor(wav_path)
            diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate})
            speaker_turns = _speaker_turns_from_diarization(diarization)

            # 3. 文字起こし
            self._report(progress, -1.0, f"文字起こしモデル({self.model_size})を読み込み中...")
            model = WhisperModel(self.model_size, device=device, compute_type=compute_type)

            self._report(progress, -1.0, "文字起こし中...")
            lang = None if self.language == "auto" else self.language
            seg_iter, info = model.transcribe(wav_path, language=lang, vad_filter=True)

            # 4. 突合
            raw_segments = []
            for seg in seg_iter:
                speaker = _assign_speaker(seg.start, seg.end, speaker_turns)
                raw_segments.append(
                    SpeakerSegment(
                        speaker=_pretty_speaker(speaker),
                        start=float(seg.start),
                        end=float(seg.end),
                        text=seg.text.strip(),
                    )
                )

            segments = _merge_adjacent(raw_segments)

            self._report(progress, 1.0, "完了")
            return TranscriptResult(
                segments=segments,
                language=getattr(info, "language", lang),
                engine=self.name,
                audio_path=audio_path,
            )
        finally:
            try:
                os.remove(wav_path)
            except OSError:
                pass


def _speaker_turns_from_diarization(diarization) -> list[tuple[float, float, str]]:
    """pyannote 3.x(Annotation) / 4.x(DiarizeOutput) 両対応で話者区間を取り出す。"""
    if hasattr(diarization, "exclusive_speaker_diarization"):
        annotation = diarization.exclusive_speaker_diarization
    elif hasattr(diarization, "speaker_diarization"):
        annotation = diarization.speaker_diarization
    else:
        annotation = diarization

    return [
        (turn.start, turn.end, speaker)
        for turn, _, speaker in annotation.itertracks(yield_label=True)
    ]


def _assign_speaker(
    start: float, end: float, turns: list[tuple[float, float, str]]
) -> str | None:
    """文字起こし区間と時間的に最も重なる話者を返す。"""
    best_speaker: str | None = None
    best_overlap = 0.0
    for t_start, t_end, speaker in turns:
        overlap = min(end, t_end) - max(start, t_start)
        if overlap > best_overlap:
            best_overlap = overlap
            best_speaker = speaker
    if best_speaker is None and turns:
        # 重なりが無い場合は中点に最も近い区間へ割り当てる
        mid = (start + end) / 2.0
        best_speaker = min(
            turns, key=lambda t: abs(((t[0] + t[1]) / 2.0) - mid)
        )[2]
    return best_speaker


def _pretty_speaker(label: str | None) -> str:
    """"SPEAKER_00" などを "話者1" 形式へ整形。"""
    if not label:
        return "話者?"
    if label.startswith("SPEAKER_"):
        try:
            return f"話者{int(label.split('_')[1]) + 1}"
        except (IndexError, ValueError):
            return label
    return label


def _merge_adjacent(segments: list[SpeakerSegment]) -> list[SpeakerSegment]:
    """連続する同一話者のセグメントを結合して読みやすくする。"""
    if not segments:
        return []
    merged = [segments[0]]
    for seg in segments[1:]:
        last = merged[-1]
        if seg.speaker == last.speaker:
            last.end = seg.end
            last.text = f"{last.text} {seg.text}".strip()
        else:
            merged.append(seg)
    return merged
