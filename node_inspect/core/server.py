"""Background daemon server managing multiple NodeInspect windows."""

import json
import os
import queue
import socket
import sys
import threading
from typing import List, Optional

from PySide6.QtCore import QObject, Signal, Qt, QTimer
from PySide6.QtWidgets import QApplication

from node_inspect.ui.main_window import MainWindow
from node_inspect.core.ipc import SERVER_INFO_PATH, CONFIG_DIR


def _force_foreground_window(win: MainWindow) -> None:
    """Force window to appear in the foreground on Windows even when spawned from a background daemon."""
    win.setWindowState((win.windowState() & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowActive)
    win.show()
    win.raise_()
    win.activateWindow()

    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            hwnd = int(win.winId())
            SW_SHOW = 5
            SW_RESTORE = 9
            HWND_TOPMOST = -1
            HWND_NOTOPMOST = -2
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_SHOWWINDOW = 0x0040

            if user32.IsIconic(hwnd):
                user32.ShowWindow(hwnd, SW_RESTORE)
            else:
                user32.ShowWindow(hwnd, SW_SHOW)

            # Temporarily toggle TOPMOST to bring window above Explorer
            user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
            user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)

            # Attach thread input to current foreground window if needed to acquire keyboard focus
            fg_hwnd = user32.GetForegroundWindow()
            fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0
            cur_tid = kernel32.GetCurrentThreadId()

            if fg_tid and fg_tid != cur_tid:
                user32.AttachThreadInput(fg_tid, cur_tid, True)
                user32.SetForegroundWindow(hwnd)
                user32.SetFocus(hwnd)
                user32.AttachThreadInput(fg_tid, cur_tid, False)
            else:
                user32.SetForegroundWindow(hwnd)
        except Exception:
            pass


class NodeInspectServer(QObject):
    """Server that listens on loopback TCP port for open file requests."""

    # Thread-safe signals to communicate with Qt main GUI thread
    request_open = Signal(str, object)
    request_stop = Signal()

    def __init__(self, app: QApplication, app_icon, parent=None):
        super().__init__(parent)
        self.app = app
        self.app_icon = app_icon
        self.windows: List[MainWindow] = []
        self.running = True
        self._cmd_queue: "queue.Queue[tuple[str, threading.Event]]" = queue.Queue()

        # Connect signals to GUI slots with QueuedConnection
        self.request_open.connect(self._handle_open_signal, Qt.ConnectionType.QueuedConnection)
        self.request_stop.connect(self.shutdown, Qt.ConnectionType.QueuedConnection)

        # Fallback timer ensures the Qt event loop wakes up and drains queued open requests
        # even when running headless with 0 open windows on Windows
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(100)
        self._poll_timer.timeout.connect(self._drain_cmd_queue)
        self._poll_timer.start()

        # Preload heavy libraries before accepting connections
        self._preload_heavy_libraries()

        # Socket setup
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("127.0.0.1", 0))
        self.port = self.sock.getsockname()[1]
        self.sock.listen(10)

        self._save_server_info()

        # Dedicated background thread to listen for incoming client connections
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def _preload_heavy_libraries(self):
        """Preload heavy libraries so subsequent file open is fast."""
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

    def _recv_line(self, conn: socket.socket) -> str:
        """Read bytes until newline or EOF."""
        chunks = []
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
        return b"".join(chunks).decode("utf-8", errors="replace").strip()

    def _listen_loop(self):
        """Run in background thread accepting TCP connections."""
        while self.running:
            try:
                conn, _ = self.sock.accept()
                conn.settimeout(3.0)
                raw_text = self._recv_line(conn)
                if not raw_text:
                    conn.close()
                    continue

                req = json.loads(raw_text)
                action = req.get("action", "open")

                if action == "open":
                    path = req.get("path") or ""
                    done_event = threading.Event()
                    self._cmd_queue.put((path, done_event))
                    # Emit signal for immediate wakeup if event loop is active
                    self.request_open.emit(path, done_event)
                    # Wait until Qt main thread actually creates and shows the window
                    if done_event.wait(timeout=2.5):
                        conn.sendall(b"OK\n")
                    else:
                        conn.sendall(b"ERR\n")
                elif action == "stop":
                    conn.sendall(b"BYE\n")
                    conn.close()
                    self.request_stop.emit()
                    break

                conn.close()
            except Exception:
                if not self.running:
                    break

    def _drain_cmd_queue(self):
        """Process any pending open requests from the queue on the Qt main thread."""
        while not self._cmd_queue.empty():
            try:
                file_path, done_event = self._cmd_queue.get_nowait()
            except queue.Empty:
                break
            if not done_event.is_set():
                try:
                    self.open_new_window(file_path if file_path else None)
                finally:
                    done_event.set()

    def _handle_open_signal(self, file_path: str, done_event: threading.Event):
        if not done_event.is_set():
            self._drain_cmd_queue()

    def open_new_window(self, file_path: Optional[str] = None) -> MainWindow:
        """Create and display a new independent MainWindow."""
        win = MainWindow()
        win.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        if self.app_icon:
            win.setWindowIcon(self.app_icon)

        # Track window and remove reference when closed
        self.windows.append(win)
        win.destroyed.connect(lambda *_: self._on_window_destroyed(win))

        _force_foreground_window(win)

        if file_path and os.path.isfile(file_path):
            win.load_file(file_path)

        # Re-assert foreground activation shortly after showing/loading
        QTimer.singleShot(50, lambda: _force_foreground_window(win))

        return win

    def _on_window_destroyed(self, win: MainWindow):
        if win in self.windows:
            self.windows.remove(win)

    def shutdown(self):
        """Shutdown the daemon server and close all windows."""
        self.running = False
        self._poll_timer.stop()
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
        threading.Timer(0.5, lambda: os._exit(0)).start()


