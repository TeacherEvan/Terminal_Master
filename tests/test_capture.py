"""Tests for capture.py."""
import pytest
from terminal_master.capture import capture
from PIL import Image  # type: ignore
import tempfile
import os
import shutil


@pytest.mark.skipif(
    shutil.which("grim") is None
    and shutil.which("scrot") is None
    and shutil.which("import") is None,
    reason="no screenshot backend available in this environment",
)
def test_capture_writes_png():
    try:
        out = capture(output_dir=tempfile.mkdtemp())
    except RuntimeError as e:
        if "compositor" in str(e).lower() or "no wl_output" in str(e).lower() or "No screenshot backend" in str(e):
            pytest.skip(f"capture backend unavailable: {e}")
        raise
    assert os.path.exists(out)
    with Image.open(out) as im:
        assert im.format == "PNG"
        assert im.size[0] > 0 and im.size[1] > 0
