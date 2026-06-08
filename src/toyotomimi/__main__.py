"""アプリのエントリポイント。"""

from __future__ import annotations

import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from . import __app_name__
    from .gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
