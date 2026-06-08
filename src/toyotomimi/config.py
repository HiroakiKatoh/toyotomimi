"""アプリ設定の読み書き。

API キー類は環境変数(.env)を優先し、なければ設定ファイルから読む。
モデルサイズや言語などの一般設定はユーザーのホーム配下に JSON で永続化する。
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # python-dotenv 未導入でも動作させる
    pass


CONFIG_DIR = Path(os.environ.get("TOYOTOMIMI_CONFIG_DIR", Path.home() / ".toyotomimi"))
CONFIG_PATH = CONFIG_DIR / "config.json"


@dataclass
class AppConfig:
    """永続化される設定。"""

    engine: str = "cloud"  # "cloud" または "local"
    language: str = "ja"  # "auto" で自動判定
    model_size: str = "small"  # ローカル(faster-whisper)のモデルサイズ
    assemblyai_api_key: str = ""
    hf_token: str = ""

    # --- 実効的なキー(環境変数を優先) ---
    @property
    def effective_assemblyai_key(self) -> str:
        return os.environ.get("ASSEMBLYAI_API_KEY") or self.assemblyai_api_key

    @property
    def effective_hf_token(self) -> str:
        return os.environ.get("HF_TOKEN") or self.hf_token


def load_config() -> AppConfig:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            known = {f for f in AppConfig.__dataclass_fields__}
            return AppConfig(**{k: v for k, v in data.items() if k in known})
        except Exception:
            # 壊れた設定は無視してデフォルトに戻す
            return AppConfig()
    return AppConfig()


def save_config(config: AppConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
