# Terminal_Master

A Python engine that turns any screen into a numbered, clickable control surface.

**What it does**
1. Captures a screenshot (`grim` on Wayland / `scrot` fallback).
2. Runs OCR (`tesseract`) and detects interactive elements — buttons, menu items, terminal options — as bounding boxes with text.
3. Numbers those elements **1 → N** top-to-bottom (lowest numeral at the top, increasing downward).
4. Exposes a clean API so a Telegram agent (this Hermes agent) can present the list to the user, receive a selection, and inject the corresponding click/key via `ydotool`.
5. Repeats — screenshot → list → act → screenshot — a controlled back-and-forth loop.

**Status:** Planning complete. See [`docs/plans/2026-08-06-terminal-master.md`](docs/plans/2026-08-06-terminal-master.md).

## Layout
```
Terminal_Master/
├── README.md
├── requirements.txt
├── docs/plans/2026-08-06-terminal-master.md
├── terminal_master/
│   ├── __init__.py
│   ├── capture.py      # screenshot
│   ├── ocr.py          # tesseract → bboxes + text
│   ├── detect.py       # filter bboxes → numbered buttons
│   ├── input.py        # ydotool click/key injection
│   └── engine.py       # orchestrates the loop, exposes API
└── tests/
```

## Requirements
- Linux (Wayland): `grim`, `tesseract` ≥ 5.0
- `ydotool` + `ydotoold` (or passwordless sudo)
- Python 3.11+
- See `requirements.txt`
