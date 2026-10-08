import sys
import os

# Ensure package root is in sys.path so it works without pip install
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from node_inspect.ui.main_window import MainWindow


def main():
    # High DPI scaling support
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # Set Windows AppUserModelID so taskbar displays application icon instead of default python.exe
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("KanekoPy.NodeInspect.Viewer")
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("NodeInspect")
    app.setOrganizationName("KanekoPy")

    from node_inspect.ui.app_icon import create_app_icon
    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)

    # Ensure ~/.node-inspect/config.json exists immediately on startup
    from node_inspect.core.config import ConfigManager
    ConfigManager.ensure_config()

    window = MainWindow()
    window.setWindowIcon(app_icon)
    window.show()

    # If file passed as CLI argument, load it directly
    if len(sys.argv) > 1:
        target_path = os.path.abspath(sys.argv[1])
        if os.path.isfile(target_path):
            window.load_file(target_path)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
