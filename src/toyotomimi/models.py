"""エンジン共通のデータ構造。

ローカル/クラウドどちらのエンジンも、解析結果をこれらの型で返す。
GUI や出力処理はエンジンの実装差を意識しなくて済む。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SpeakerSegment:
    """1 人の話者による連続した発話区間。"""

    speaker: str
    start: float  # 秒
    end: float  # 秒
    text: str

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class TranscriptResult:
    """解析全体の結果。"""

    segments: list[SpeakerSegment] = field(default_factory=list)
    language: str | None = None
    engine: str | None = None
    audio_path: str | None = None

    @property
    def speakers(self) -> list[str]:
        """登場した話者ラベルを初出順で返す。"""
        seen: list[str] = []
        for seg in self.segments:
            if seg.speaker not in seen:
                seen.append(seg.speaker)
        return seen

    @property
    def full_text(self) -> str:
        """話者ラベルを付けた読みやすいテキスト。"""
        return "\n".join(f"{seg.speaker}: {seg.text}" for seg in self.segments)
