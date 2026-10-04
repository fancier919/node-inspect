"""Entry point for NodeInspect application."""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from node_inspect.ui.main_window import MainWindow


def main():
    # High DPI scaling support
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("NodeInspect")
    app.setOrganizationName("KanekoPy")

    window = MainWindow()
    window.show()

    # If file passed as CLI argument, load it directly
    if len(sys.argv) > 1:
        target_path = os.path.abspath(sys.argv[1])
        if os.path.isfile(target_path):
            window.load_file(target_path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
