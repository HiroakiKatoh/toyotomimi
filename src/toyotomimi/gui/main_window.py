"""メインウィンドウ。

ファイル選択 → エンジン選択 → 実行 → 進捗 → 結果表示 → 保存 の一連を提供する。
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .. import __app_name__, __version__
from ..audio import ffmpeg_available
from ..config import AppConfig, load_config, save_config
from ..export import save as save_result
from ..models import TranscriptResult
from .settings_dialog import SettingsDialog
from .worker import TranscribeWorker

_ENGINE_CHOICES = [
    ("クラウド (AssemblyAI / 高速・高精度)", "cloud"),
    ("ローカル (faster-whisper + pyannote / オフライン)", "local"),
]
_AUDIO_FILTER = "音声/動画 (*.mp3 *.wav *.m4a *.flac *.ogg *.mp4 *.aac);;すべて (*.*)"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config: AppConfig = load_config()
        self._audio_path: str | None = None
        self._result: TranscriptResult | None = None
        self._worker: TranscribeWorker | None = None

        self.setWindowTitle(f"{__app_name__} v{__version__}")
        self.resize(820, 620)
        self._build_ui()
        self._build_menu()
        self._sync_engine_combo()

    # ---------- UI 構築 ----------
    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        title = QLabel(f"{__app_name__} — 話者分離つき文字起こし")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        root.addWidget(title)

        # ファイル選択行
        file_row = QHBoxLayout()
        self.file_label = QLabel("音声ファイルが選択されていません")
        self.file_label.setStyleSheet("color: gray;")
        choose_btn = QPushButton("ファイルを選択...")
        choose_btn.clicked.connect(self._choose_file)
        file_row.addWidget(self.file_label, stretch=1)
        file_row.addWidget(choose_btn)
        root.addLayout(file_row)

        # エンジン選択行
        engine_row = QHBoxLayout()
        engine_row.addWidget(QLabel("処理方法:"))
        self.engine_combo = QComboBox()
        for label, value in _ENGINE_CHOICES:
            self.engine_combo.addItem(label, value)
        self.engine_combo.currentIndexChanged.connect(self._on_engine_changed)
        engine_row.addWidget(self.engine_combo, stretch=1)
        self.run_btn = QPushButton("解析する")
        self.run_btn.clicked.connect(self._run)
        engine_row.addWidget(self.run_btn)
        root.addLayout(engine_row)

        # 進捗
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        root.addWidget(self.progress)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 12px;")
        root.addWidget(self.status_label)

        # 結果表示
        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        self.result_view.setPlaceholderText(
            "解析結果がここに表示されます。\n話者ごとに分けて文字起こしされます。"
        )
        root.addWidget(self.result_view, stretch=1)

        # 保存行
        save_row = QHBoxLayout()
        save_row.addStretch(1)
        self.save_btn = QPushButton("結果を保存...")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._save)
        save_row.addWidget(self.save_btn)
        root.addLayout(save_row)

        self.setCentralWidget(central)

        if not ffmpeg_available():
            self.status_label.setText(
                "警告: ffmpeg が見つかりません。音声変換に必要なため導入を推奨します。"
            )
            self.status_label.setStyleSheet("color: #c0392b; font-size: 12px;")

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("ファイル")
        settings_action = QAction("設定...", self)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)
        menu.addSeparator()
        quit_action = QAction("終了", self)
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)

    def _sync_engine_combo(self) -> None:
        idx = self.engine_combo.findData(self.config.engine)
        if idx >= 0:
            self.engine_combo.setCurrentIndex(idx)

    # ---------- イベント ----------
    def _on_engine_changed(self) -> None:
        self.config.engine = self.engine_combo.currentData()
        save_config(self.config)

    def _choose_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "音声ファイルを選択", "", _AUDIO_FILTER
        )
        if path:
            self._audio_path = path
            self.file_label.setText(path)
            self.file_label.setStyleSheet("")

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            dialog.apply_to(self.config)
            save_config(self.config)
            self._sync_engine_combo()

    def _run(self) -> None:
        if not self._audio_path:
            QMessageBox.warning(self, __app_name__, "先に音声ファイルを選択してください。")
            return
        if self._worker and self._worker.isRunning():
            return

        self.config.engine = self.engine_combo.currentData()
        save_config(self.config)

        self._set_running(True)
        self.result_view.clear()

        self._worker = TranscribeWorker(self._audio_path, self.config)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_progress(self, ratio: float, message: str) -> None:
        if ratio < 0:
            self.progress.setRange(0, 0)  # 不定(マーキー)表示
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(int(ratio * 100))
        self.status_label.setText(message)

    def _on_finished(self, result: TranscriptResult) -> None:
        self._result = result
        self.result_view.setPlainText(result.full_text)
        self.status_label.setText(
            f"完了 — 話者 {len(result.speakers)} 名 / {len(result.segments)} 区間"
        )
        self.save_btn.setEnabled(True)
        self._set_running(False)

    def _on_failed(self, message: str) -> None:
        self.status_label.setText("エラー")
        self._set_running(False)
        QMessageBox.critical(self, __app_name__, message)

    def _save(self) -> None:
        if not self._result:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "結果を保存",
            "transcript.txt",
            "テキスト (*.txt);;SRT字幕 (*.srt);;JSON (*.json)",
        )
        if not path:
            return
        try:
            save_result(self._result, path)
            self.status_label.setText(f"保存しました: {path}")
        except Exception as exc:
            QMessageBox.critical(self, __app_name__, f"保存に失敗しました: {exc}")

    def _set_running(self, running: bool) -> None:
        self.run_btn.setEnabled(not running)
        self.engine_combo.setEnabled(not running)
        self.progress.setVisible(running)
        if not running:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
