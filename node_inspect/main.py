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

    # Handle command-line arguments for server mode / stop
    args = sys.argv[1:]

    # 1. Check if user explicitly wants to stop running server
    if "--stop" in args:
        from node_inspect.core.ipc import stop_server
        if stop_server():
            print("NodeInspect server stopped.")
        else:
            print("No running NodeInspect server found.")
        sys.exit(0)

    is_server_mode = "--server" in args
    target_file = None
    for arg in args:
        if arg not in ("--server", "--daemon"):
            clean = arg.strip().strip('"').strip("'")
            if os.path.isfile(clean):
                target_file = clean
                break

    # 2. If not running in explicit server mode, check if a daemon server is already active
    # If active, delegate opening to it and exit immediately (10ms startup!)
    if not is_server_mode:
        from node_inspect.core.ipc import send_to_server
        if send_to_server(target_file):
            # Successfully sent to server, exit immediately
            sys.exit(0)

    # 3. Otherwise, launch GUI / server
    app = QApplication(sys.argv)
    app.setApplicationName("NodeInspect")
    app.setOrganizationName("KanekoPy")

    from node_inspect.ui.app_icon import create_app_icon
    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)

    # Ensure ~/.node-inspect/config.json exists immediately on startup
    from node_inspect.core.config import ConfigManager
    ConfigManager.ensure_config()

    from node_inspect.core.server import NodeInspectServer
    server = NodeInspectServer(app, app_icon)

    # If --server mode without files, just run in background waiting for requests
    # If normal startup, open initial window
    if not is_server_mode or target_file:
        server.open_new_window(target_file)

    # Keep server running even if windows close when in --server mode
    if is_server_mode:
        app.setQuitOnLastWindowClosed(False)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
