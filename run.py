"""Standalone runner for NodeInspect without pip installation."""

import sys
import os

# Automatically add repository root to sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Ultralight check: if server is running, forward request instantly (in ~10ms) without loading PySide6/GUI
if "--server" not in sys.argv and "--stop" not in sys.argv:
    from node_inspect.core.ipc import send_to_server
    target_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if send_to_server(target_arg):
        sys.exit(0)

from node_inspect.main import main

if __name__ == "__main__":
    main()
