"""Client-Server IPC and daemon management for fast startup."""

import json
import os
import socket
import sys
from typing import Optional

CONFIG_DIR = os.path.expanduser("~/.node-inspect")
SERVER_INFO_PATH = os.path.join(CONFIG_DIR, "server.json")


def _allow_set_foreground_window(server_pid: int) -> None:
    """Delegate Windows foreground window permission from client process to daemon server."""
    if sys.platform == "win32" and server_pid > 0:
        try:
            import ctypes
            ctypes.windll.user32.AllowSetForegroundWindow(int(server_pid))
        except Exception:
            pass


def send_to_server(file_path: Optional[str] = None, timeout: float = 3.0) -> bool:
    """Send an open file request to the running daemon server.

    Returns:
        True if the message was successfully delivered and acknowledged by an active server,
        False otherwise.
    """
    if not os.path.isfile(SERVER_INFO_PATH):
        return False

    try:
        with open(SERVER_INFO_PATH, "r", encoding="utf-8") as f:
            info = json.load(f)
        port = int(info.get("port", 0))
        server_pid = int(info.get("pid", 0))
        if port <= 0:
            return False

        # Grant foreground activation rights to the server before sending request
        _allow_set_foreground_window(server_pid)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(("127.0.0.1", port))

        payload = {
            "action": "open",
            "path": os.path.abspath(file_path) if file_path else "",
        }
        sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        resp = sock.recv(1024)
        sock.close()
        if resp.strip() == b"OK":
            # Give the server window a brief moment to complete foreground activation
            # while this client process is still alive
            import time
            time.sleep(0.08)
            return True
        return False
    except Exception:
        # Server is dead or unreachable, clean up stale info
        try:
            if os.path.isfile(SERVER_INFO_PATH):
                os.remove(SERVER_INFO_PATH)
        except Exception:
            pass
        return False


def stop_server(timeout: float = 2.0) -> bool:
    """Send shutdown command to running server."""
    if not os.path.isfile(SERVER_INFO_PATH):
        return False

    try:
        with open(SERVER_INFO_PATH, "r", encoding="utf-8") as f:
            info = json.load(f)
        port = int(info.get("port", 0))

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(("127.0.0.1", port))

        payload = {"action": "stop"}
        sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        resp = sock.recv(1024)
        sock.close()
        return True
    except Exception:
        try:
            if os.path.isfile(SERVER_INFO_PATH):
                os.remove(SERVER_INFO_PATH)
        except Exception:
            pass
        return False

