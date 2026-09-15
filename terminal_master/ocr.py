"""OCR via tesseract.

Uses pytesseract if installed; otherwise shells out to the `tesseract` CLI and
parses TSV (verified working on this host: tesseract 5.3.4). Returns word-level
boxes with geometry + confidence.
"""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WordBox:
    text: str
    left: int
    top: int
    width: int
    height: int
    conf: float

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def center_x(self) -> int:
        return self.left + self.width // 2

    @property
    def center_y(self) -> int:
        return self.top + self.height // 2


def ocr_words(path: str) -> list[WordBox]:
    """Return word-level boxes from an image path."""
    if shutil.which("tesseract") is None:
        raise RuntimeError("tesseract binary not found on PATH.")

    # Prefer pytesseract if present
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore

        data = pytesseract.image_to_data(
            Image.open(path), output_type=pytesseract.Output.DICT
        )
        boxes: list[WordBox] = []
        n = len(data["text"])
        for i in range(n):
            txt = (data["text"][i] or "").strip()
            if not txt:
                continue
            try:
                conf = float(data["conf"][i])
            except (ValueError, TypeError):
                conf = -1.0
            if conf < 0:
                continue
            boxes.append(
                WordBox(
                    text=txt,
                    left=int(data["left"][i]),
                    top=int(data["top"][i]),
                    width=int(data["width"][i]),
                    height=int(data["height"][i]),
                    conf=conf,
                )
            )
        return boxes
    except ImportError:
        pass

    # Fallback: CLI TSV
    import os
    import tempfile

    # TSV block_num for a single word (page=1, block=5, par=0, line=0, word=N)
    WORD_BLOCK_NUM = 5

    fd, base = tempfile.mkstemp()
    os.close(fd)
    tsv_path = base + ".tsv"
    try:
        res = subprocess.run(
            ["tesseract", path, base, "--psm", "6", "tsv"],
            check=False,
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            raise RuntimeError(f"tesseract failed: {res.stderr.strip()}")
        boxes = []
        with open(tsv_path) as f:
            next(f, None)  # header
            for line in f:
                cols = line.rstrip("\n").split("\t")
                if len(cols) < 12 or cols[0] != str(WORD_BLOCK_NUM):
                    continue
                try:
                    conf = float(cols[10])
                except ValueError:
                    continue
                txt = cols[11].strip()
                if not txt or conf < 0:
                    continue
                boxes.append(
                    WordBox(
                        text=txt,
                        left=int(cols[6]),
                        top=int(cols[7]),
                        width=int(cols[8]),
                        height=int(cols[9]),
                        conf=conf,
                    )
                )
        return boxes
    finally:
        Path(base).unlink(missing_ok=True)
        Path(tsv_path).unlink(missing_ok=True)
