"""文字起こしエンジン群。"""

from __future__ import annotations

from ..config import AppConfig
from .base import EngineError, ProgressCallback, TranscriptionEngine

__all__ = [
    "TranscriptionEngine",
    "ProgressCallback",
    "EngineError",
    "build_engine",
]


def build_engine(config: AppConfig) -> TranscriptionEngine:
    """設定に基づいてエンジンを生成する。"""
    if config.engine == "local":
        from .local_engine import LocalEngine

        return LocalEngine(
            hf_token=config.effective_hf_token,
            model_size=config.model_size,
            language=config.language,
        )
    if config.engine == "cloud":
        from .cloud_engine import CloudEngine

        return CloudEngine(
            api_key=config.effective_assemblyai_key,
            language=config.language,
        )
    raise EngineError(f"不明なエンジン: {config.engine}")
