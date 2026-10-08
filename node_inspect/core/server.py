"""Background daemon server managing multiple NodeInspect windows."""

import json
import os
import socket
import sys
import threading
from typing import List, Optional

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import QApplication

from node_inspect.ui.main_window import MainWindow
from node_inspect.core.ipc import SERVER_INFO_PATH, CONFIG_DIR


class NodeInspectServer(QObject):
    """Server that listens on loopback TCP port for open file requests."""

    # Thread-safe signals to communicate with Qt main GUI thread
    request_open = Signal(str)
    request_stop = Signal()

    def __init__(self, app: QApplication, app_icon, parent=None):
        super().__init__(parent)
        self.app = app
        self.app_icon = app_icon
        self.windows: List[MainWindow] = []
        self.running = True

        # Connect signals to GUI slots
        self.request_open.connect(self._handle_open_signal)
        self.request_stop.connect(self.shutdown)

        # Socket setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.port = self.sock.getsockname()[1]
        self.sock.listen(10)

        self._save_server_info()

        # Dedicated background thread to listen without any Qt event loop lag
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

        self._preload_heavy_libraries()

    def _preload_heavy_libraries(self):
        """Preload heavy libraries in background so subsequent file open is instant."""
        try:
            import pandas
            import pyarrow.parquet
            import numpy
        except Exception:
            pass

    def _save_server_info(self):
        """Save server port and pid to ~/.node-inspect/server.json."""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        info = {
            "port": self.port,
            "pid": os.getpid(),
        }
        with open(SERVER_INFO_PATH, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2)

    def _remove_server_info(self):
        """Clean up server info file on exit."""
        try:
            if os.path.isfile(SERVER_INFO_PATH):
                os.remove(SERVER_INFO_PATH)
        except Exception:
            pass

    def _listen_loop(self):
        """Run in background thread accepting TCP connections."""
        while self.running:
            try:
                conn, _ = self.sock.accept()
                conn.settimeout(3.0)
                raw = conn.recv(4096)
                if not raw:
                    conn.close()
                    continue

                req = json.loads(raw.decode("utf-8").strip())
                action = req.get("action", "open")

                if action == "open":
                    path = req.get("path") or ""
                    # Dispatch to Qt Main thread safely via Signal
                    self.request_open.emit(path)
                    conn.sendall(b"OK\n")
                elif action == "stop":
                    conn.sendall(b"BYE\n")
                    conn.close()
                    self.request_stop.emit()
                    break

                conn.close()
            except Exception:
                if not self.running:
                    break

    def _handle_open_signal(self, file_path: str):
        self.open_new_window(file_path if file_path else None)

    def open_new_window(self, file_path: Optional[str] = None) -> MainWindow:
        """Create and display a new independent MainWindow."""
        win = MainWindow()
        if self.app_icon:
            win.setWindowIcon(self.app_icon)

        # Track window and remove reference when closed
        self.windows.append(win)
        win.destroyed.connect(lambda: self._on_window_destroyed(win))

        win.show()
        win.raise_()
        win.activateWindow()

        if file_path and os.path.isfile(file_path):
            win.load_file(file_path)

        return win

    def _on_window_destroyed(self, win: MainWindow):
        if win in self.windows:
            self.windows.remove(win)

    def shutdown(self):
        """Shutdown the daemon server and close all windows."""
        self.running = False
        self._remove_server_info()
        try:
            self.sock.close()
        except Exception:
            pass
        for win in list(self.windows):
            try:
                win.close()
            except Exception:
                pass
        self.app.exit(0)
        # Force terminate process if background thread hangs
        import threading
        threading.Timer(0.5, lambda: os._exit(0)).start()

