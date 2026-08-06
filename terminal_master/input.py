"""Input injection for Terminal_Master via ydotool.

`ydotool` needs its daemon (ydotoold) OR root. This host has passwordless sudo,
so we fall back to `sudo ydotool` when the daemon socket is absent.
"""
from __future__ import annotations

import os
import subprocess

SOCKET = "/tmp/.ydotool_socket"


def _ydotool_prefix() -> list[str]:
    if os.path.exists(SOCKET):
        return ["ydotool"]
    # No daemon socket -> need root
    return ["sudo", "-n", "ydotool"]


def click(element) -> bool:
    """Click at an element's center via ydotool mouse move+click."""
    x, y = element.center_x, element.center_y
    prefix = _ydotool_prefix()
    # move then click (left button = 0xC0 down/up)
    cmds = [
        [*prefix, "mousemove", "-x", str(x), "-y", str(y)],
        [*prefix, "click", "0xC0"],
    ]
    for c in cmds:
        res = subprocess.run(c, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(
                f"ydotool failed: {' '.join(c)} -> {res.stderr.strip()}"
            )
    return True


def press_key(keys: str) -> bool:
    """Type a key sequence, e.g. '24:1 24:0' or a single key name."""
    prefix = _ydotool_prefix()
    res = subprocess.run([*prefix, "key", keys], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ydotool key failed: {res.stderr.strip()}")
    return True


def type_text(text: str) -> bool:
    prefix = _ydotool_prefix()
    res = subprocess.run([*prefix, "type", text], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ydotool type failed: {res.stderr.strip()}")
    return True
