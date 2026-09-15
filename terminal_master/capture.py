"""Screen capture for Terminal_Master.

Primary path: `grim` (Wayland). Falls back to `scrot` (X11) then ImageMagick
`import`. Returns an absolute PNG path.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def capture(output_dir: str | None = None) -> str:
    """Capture the screen and return the PNG path.

    Raises RuntimeError if no capture backend is available.
    """
    out_dir = Path(output_dir or "screenshots")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "shot.png"

    if shutil.which("grim"):
        # Wayland: capture full screen (no output arg = all outputs)
        cmd = ["grim", str(out_path)]
    elif shutil.which("scrot"):
        cmd = ["scrot", "--silent", str(out_path)]
    elif shutil.which("import"):
        cmd = ["import", "-window", "root", str(out_path)]
    else:
        raise RuntimeError("No screenshot backend found (need grim/scrot/import).")

    res = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if res.returncode != 0 or not out_path.exists():
        raise RuntimeError(f"Capture failed: {res.stderr.strip() or 'no output file'}")

    return str(out_path)

