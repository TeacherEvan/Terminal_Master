"""Tests for ocr.py using a rendered fixture (no real screen needed)."""
from terminal_master.ocr import ocr_words
from PIL import Image, ImageDraw, ImageFont  # type: ignore
import tempfile
from pathlib import Path


def test_ocr_finds_text():
    # Real terminal text is rendered at a legible size; use a TTF font so
    # tesseract keeps the word space (matches real-world behavior).
    import glob

    fonts = glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)
    font = ImageFont.truetype(fonts[0], 36) if fonts else ImageFont.load_default()
    img = Image.new("RGB", (800, 240), "black")
    d = ImageDraw.Draw(img)
    d.text((20, 80), "Hello World", fill="white", font=font)
    p = tempfile.mktemp(suffix=".png")
    img.save(p)
    boxes = ocr_words(p)
    texts = " ".join(b.text for b in boxes)
    assert "Hello" in texts and "World" in texts


def test_ocr_empty_image():
    img = Image.new("RGB", (200, 100), "black")
    p = tempfile.mktemp(suffix=".png")
    img.save(p)
    boxes = ocr_words(p)
    assert boxes == []


def test_tsv_fallback_parses_and_cleans_up(tmp_path, monkeypatch):
    """CLI fallback path: tesseract TSV parsed, temp file removed after return."""
    import terminal_master.ocr as ocr

    # Force the ImportError branch: block the pytesseract module so the
    # `import pytesseract` inside ocr_words raises ImportError.
    monkeypatch.setitem(__import__("sys").modules, "pytesseract", None)

    tsv = (
        "level	page_num	block_num	par_num	line_num	word_num	left	top	"
        "width	height	conf	text\n"
        "5	1	5	0	0	1	10	20	80	30	95.0	OK\n"
    )
    base = str(tmp_path / "out")

    calls = []

    def fake_run(cmd, *a, **kw):
        calls.append(cmd)
        m = type("M", (), {"returncode": 0, "stderr": ""})()
        # Write the TSV file tesseract would have produced at the path the
        # code passed (cmd[2] is the base name tesseract appends .tsv to).
        Path(cmd[2] + ".tsv").write_text(tsv)
        return m

    monkeypatch.setattr(ocr.subprocess, "run", fake_run)

    boxes = ocr.ocr_words("dummy.png")
    assert len(boxes) == 1
    assert boxes[0].text == "OK"
    assert boxes[0].left == 10 and boxes[0].top == 20
    assert not Path(base).exists(), "temp base must be cleaned up"
    assert not Path(base + ".tsv").exists(), "temp TSV must be cleaned up"
    assert calls[0][0] == "tesseract"
    assert calls[0][1] == "dummy.png"
    assert "--psm" in calls[0] and "6" in calls[0] and "tsv" in calls[0]
    # tesseract appends .tsv to the base name it was given
    assert Path(calls[0][2] + ".tsv").exists() is False  # cleaned up
