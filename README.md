# Terminal_Master

A Python engine that turns any screen into a numbered, clickable control surface.

**What it does**
1. Captures a screenshot (`grim` on Wayland).
2. Runs OCR (`tesseract`) → word boxes.
3. Clusters words into **options** and numbers them **1 → N top-to-bottom**
   (one number per interactive option, not per word).
4. Exposes `run_once()` + `act(number)`; the Telegram agent shows the list, you
   pick a number, the engine clicks via `ydotool`. Loop repeats.
5. Preprocessing upsamples 2× to recover small terminal text.

**Status:** Implemented MVP. Tests green (15 passed, 1 skipped — capture needs a
real Wayland compositor, not the agent sandbox). Milestone 4 engine contract
covered by `tests/test_engine.py` (scaling, lookup, session-loop).

## Layout
```
Terminal_Master/
├── README.md
├── requirements.txt
├── docs/plans/2026-08-06-terminal-master.md
├── terminal_master/
│   ├── __init__.py
│   ├── capture.py      # grim/scrot/import screenshot
│   ├── ocr.py          # tesseract -> word boxes (pytesseract + CLI fallback)
│   ├── detect.py       # cluster words -> numbered options (top->bottom)
│   ├── input.py        # ydotool click/key/type (sudo fallback if no daemon)
│   └── engine.py       # run_once() / act() / session_loop()
└── tests/
```

## Requirements
- Linux (Wayland): `grim`, `tesseract` ≥ 5.0
- `ydotool` (+ `ydotoold` recommended, or passwordless sudo)
- Python 3.11+, `Pillow`

## Model note
Free LLM for any generation: `nvidia/nemotron-3-ultra:free` (Nous Portal, no key).
OpenRouter not wired — needs `OPENROUTER_API_KEY`.
