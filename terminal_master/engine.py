"""Terminal_Master engine — orchestrates capture -> OCR -> detect -> act.

The Telegram agent (this Hermes agent) calls `run_once()` to get a numbered
option list, shows it to the user, then calls `act(number)` to click. No
Telegram code lives here — the agent is the bridge.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image  # type: ignore

from .capture import capture
from .detect import NumberedElement, detect_buttons
from .input import click
from .ocr import ocr_words

# Supersample factor: render at higher resolution before OCR to recover small
# terminal text (proved: low-DPI terminal menus get mangled by tesseract).
UPSCALE = 2


def _preprocess(path: str) -> str:
    """Upscale + grayscale for cleaner OCR. Returns temp PNG path."""
    img = Image.open(path).convert("L")
    if UPSCALE > 1:
        img = img.resize(
            (img.width * UPSCALE, img.height * UPSCALE), Image.Resampling.LANCZOS
        )
    out = tempfile.mktemp(suffix=".png")
    img.save(out)
    return out


def run_once(strict: bool = False, output_dir: str | None = None) -> list[NumberedElement]:
    """Capture screen, OCR, detect + number interactive options (1..N top->bottom)."""
    raw = capture(output_dir=output_dir)
    pre = _preprocess(raw)
    words = ocr_words(pre)
    with Image.open(raw) as im:
        w, h = im.size
    elements = detect_buttons(words, w * UPSCALE, h * UPSCALE, strict=strict)
    # Scale centers back to original image coordinates
    for el in elements:
        el.center_x //= UPSCALE
        el.center_y //= UPSCALE
        el.left //= UPSCALE
        el.top //= UPSCALE
        el.width //= UPSCALE
        el.height //= UPSCALE
    Path(pre).unlink(missing_ok=True)
    return elements


def act(number: int, elements: list[NumberedElement]) -> bool:
    """Click the option with the given number."""
    for el in elements:
        if el.number == number:
            return click(el)
    raise ValueError(f"No option numbered {number}")


def session_loop(strict: bool = False):
    """Generator: yields numbered lists; send() a number to act, then re-captures."""
    elements = run_once(strict=strict)
    while True:
        choice = yield elements
        if choice is None:
            break
        act(choice, elements)
        elements = run_once(strict=strict)  # re-capture for next turn


__all__ = ["run_once", "act", "session_loop", "NumberedElement"]
