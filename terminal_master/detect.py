"""Element detection + numbering for Terminal_Master.

Clusters OCR word boxes into OPTION rows (not individual words), then numbers
them 1..N top-to-bottom so a user picks one option per number. Includes a
heuristic to drop non-interactive noise (window titles, body prose).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .ocr import WordBox


@dataclass
class NumberedElement:
    number: int
    text: str
    left: int
    top: int
    width: int
    height: int
    center_x: int
    center_y: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


def _looks_interactive(text: str) -> bool:
    """Heuristic: button/option-like text, not prose or bare title."""
    if not text:
        return False
    # Must contain at least one alphanumerics
    if not any(ch.isalnum() for ch in text):
        return False
    # Drop very long strings (paragraphs / window captions)
    if len(text) > 60:
        return False
    return True


def detect_buttons(
    boxes: list[WordBox],
    img_width: int,
    img_height: int,
    strict: bool = False,
    line_gap: int = 8,
) -> list[NumberedElement]:
    """Cluster words into option rows and number them top->bottom (1..N).

    Args:
        boxes: word-level OCR boxes.
        img_width, img_height: source image size (for width heuristics).
        strict: if True, keep only clearly button-sized boxes (narrower than
                0.6x image width, height in [12,120]).
        line_gap: vertical px tolerance to merge words on the same line.
    """
    # Filter by confidence + interactivity
    words = [b for b in boxes if b.conf > 40 and _looks_interactive(b.text)]
    if strict:
        words = [
            b
            for b in words
            if b.width < 0.6 * img_width and 12 <= b.height <= 120
        ]
    words.sort(key=lambda b: (b.top, b.left))

    # Cluster into lines by vertical overlap
    lines: list[list[WordBox]] = []
    current: list[WordBox] = []
    current_bottom = -1
    for w in words:
        if not current or w.top <= current_bottom + line_gap:
            current.append(w)
            current_bottom = max(current_bottom, w.bottom)
        else:
            lines.append(current)
            current = [w]
            current_bottom = w.bottom
    if current:
        lines.append(current)

    # Sort lines top->bottom, assign numbers
    lines.sort(key=lambda grp: min(w.top for w in grp))
    elements: list[NumberedElement] = []
    for i, grp in enumerate(lines, start=1):
        grp.sort(key=lambda w: w.left)
        text = " ".join(w.text for w in grp)
        left = min(w.left for w in grp)
        top = min(w.top for w in grp)
        right = max(w.right for w in grp)
        bottom = max(w.bottom for w in grp)
        elements.append(
            NumberedElement(
                number=i,
                text=text,
                left=left,
                top=top,
                width=right - left,
                height=bottom - top,
                center_x=(left + right) // 2,
                center_y=(top + bottom) // 2,
            )
        )
    return elements
