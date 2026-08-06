"""Tests for ocr.py using a rendered fixture (no real screen needed)."""
from terminal_master.ocr import ocr_words
from PIL import Image, ImageDraw, ImageFont  # type: ignore
import tempfile


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
