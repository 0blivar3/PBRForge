from __future__ import annotations
import sys
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow
from app.theme import DARK_THEME

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PBRForge")
    app.setOrganizationName("PBRForge")
    app.setStyleSheet(DARK_THEME)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
