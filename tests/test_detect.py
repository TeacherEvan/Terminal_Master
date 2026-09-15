"""Tests for detect.py — option-level clustering + top->bottom numbering."""
from terminal_master.detect import detect_buttons
from terminal_master.ocr import WordBox


def _box(text, top, left=10, width=80, height=20, conf=90.0):
    return WordBox(text=text, left=left, top=top, width=width, height=height, conf=conf)


def test_numbers_top_to_bottom():
    # Three stacked options; each is one line of words
    boxes = [
        _box("1) Connect to server", top=30),
        _box("2) Disconnect", top=90),
        _box("3) Show logs", top=150),
    ]
    els = detect_buttons(boxes, img_width=640, img_height=320)
    assert len(els) == 3
    assert [e.number for e in els] == [1, 2, 3]
    assert els[0].top < els[1].top < els[2].top
    assert els[0].text == "1) Connect to server"
    assert els[2].text == "3) Show logs"


def test_multiword_option_clusters_into_one_number():
    # An option spanning two words on the same line = ONE number
    boxes = [
        _box("Connect", top=30, left=10, width=70),
        _box("to server", top=30, left=90, width=80),
        _box("Quit", top=90, left=10, width=40),
    ]
    els = detect_buttons(boxes, img_width=640, img_height=320)
    assert len(els) == 2
    assert els[0].number == 1 and "Connect to server" in els[0].text
    assert els[1].number == 2 and els[1].text == "Quit"


def test_drops_long_prose():
    boxes = [_box("This is a very long paragraph of body text that should not be an option", top=30, width=500)]
    els = detect_buttons(boxes, img_width=640, img_height=320)
    assert els == []
