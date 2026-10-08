"""Client-Server IPC and daemon management for ultra-fast startup."""

import json
import os
import socket
import sys
from typing import Optional

CONFIG_DIR = os.path.expanduser("~/.node-inspect")
SERVER_INFO_PATH = os.path.join(CONFIG_DIR, "server.json")


def send_to_server(file_path: Optional[str] = None, timeout: float = 1.0) -> bool:
    """Send an open file request to the running daemon server.

    Returns:
        True if the message was successfully delivered to an active server, False otherwise.
    """
    if not os.path.isfile(SERVER_INFO_PATH):
        return False

    try:
        with open(SERVER_INFO_PATH, "r", encoding="utf-8") as f:
            info = json.load(f)
        port = int(info.get("port", 0))
        if port <= 0:
            return False

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
        return resp.strip() == b"OK"
    except Exception:
        # Server is dead or unreachable, clean up stale info
        try:
            if os.path.isfile(SERVER_INFO_PATH):
                os.remove(SERVER_INFO_PATH)
        except Exception:
            pass
        return False


def stop_server(timeout: float = 1.5) -> bool:
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
