"""設定ダイアログ: APIキー/トークン・モデルサイズ・言語。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from ..config import AppConfig

_LANGUAGES = [
    ("日本語", "ja"),
    ("英語", "en"),
    ("自動判定", "auto"),
]
_MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.setMinimumWidth(440)
        self._config = config

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.assemblyai_edit = QLineEdit(config.assemblyai_api_key)
        self.assemblyai_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.assemblyai_edit.setPlaceholderText("クラウド処理用 (環境変数優先)")
        form.addRow("AssemblyAI API キー", self.assemblyai_edit)

        self.hf_edit = QLineEdit(config.hf_token)
        self.hf_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.hf_edit.setPlaceholderText("ローカル処理用 (環境変数優先)")
        form.addRow("Hugging Face トークン", self.hf_edit)

        self.language_combo = QComboBox()
        for label, code in _LANGUAGES:
            self.language_combo.addItem(label, code)
        self._select_combo(self.language_combo, config.language)
        form.addRow("言語", self.language_combo)

        self.model_combo = QComboBox()
        self.model_combo.addItems(_MODEL_SIZES)
        if config.model_size in _MODEL_SIZES:
            self.model_combo.setCurrentText(config.model_size)
        form.addRow("ローカルモデルサイズ", self.model_combo)

        layout.addLayout(form)

        hint = QLabel(
            "環境変数 (.env の ASSEMBLYAI_API_KEY / HF_TOKEN) が設定されていれば\n"
            "そちらが優先されます。モデルサイズはローカル処理時のみ使用します。"
        )
        hint.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _select_combo(combo: QComboBox, data: str) -> None:
        idx = combo.findData(data)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def apply_to(self, config: AppConfig) -> None:
        """ダイアログの内容を設定オブジェクトへ反映する。"""
        config.assemblyai_api_key = self.assemblyai_edit.text().strip()
        config.hf_token = self.hf_edit.text().strip()
        config.language = self.language_combo.currentData()
        config.model_size = self.model_combo.currentText()
