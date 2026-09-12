# Terminal_Master Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

> **STATUS: COMPLETE** — verified 2026-09-12 by surgical-implementation run.
> All 5 milestones implemented as live code; 16 tests passed / 1 skipped
> (Wayland-only capture, environment). Gate: PASS. Tree matches origin/master.
> Audit artifacts: docs/.scratch-audit/debrief-2026-09-12.txt,
> docs/.scratch-audit/traceability-2026-09-12.txt. No re-implementation needed.

**Goal:** Build a Python engine that screenshots the screen, OCR-detects interactive
elements (buttons / terminal options), labels them 1→N top-to-bottom, and lets a
Telegram agent drive clicks/keys via `ydotool` in a back-and-forth loop.

**Architecture:** A local Python engine (no GUI of its own) captures + OCRs the screen,
returns a numbered element list via a function API. The existing Hermes/Telegram agent
calls that API, shows the list to the user in Telegram, sends the chosen number back, and
the engine injects the input. A single `Engine.run_once()` returns the numbered list;
`Engine.act(index)` performs the click. The agent owns the conversation.

**Tech Stack:** Python 3.11, `grim` (Wayland capture), `tesseract` 5.3.4 (OCR via TSV
bounding boxes), `Pillow` + `pytesseract`, `ydotool`/`ydotoold` (input injection),
Hermes Telegram channel (already connected) for the human-in-the-loop.

**Effort:** ~1.5 weeks | **Surfaces touched:** 1 package | **New tables:** 0 | **Feature flag:** n/a

---

## Environment Facts (verified 2026-08-06)
- `grim` present at `/usr/bin/grim` → primary capture path.
- `tesseract` 5.3.4 present; TSV bbox output confirmed working.
- `pytesseract` NOT installed → pin in requirements; code path also supports calling
  `tesseract` CLI with `--psm 6 tsv` as fallback (already verified to emit `left/top/width/height/text`).
- `ydotool` present but needs `ydotoold` socket or root. Agent has passwordless sudo →
  wrapper runs `sudo ydotool` when no socket. **Risk** — see table.
- `import` (ImageMagick) present as secondary capture if `grim`/`scrot` absent.
- Email delivery target: `ewiebotha@gmail.com` via `himalaya` (gmail).
- Telegram: this agent already mediates Telegram; bot token is masked in `.env`, so the
  engine does NOT need its own Telegram bot — the agent is the bridge.

---

## Milestone Timeline

### Milestone 1: Capture + OCR core (no numbering yet)
- `terminal_master/capture.py` — `capture() -> path` using `grim`.
- `terminal_master/ocr.py` — `ocr_boxes(path) -> list[Box]` via `pytesseract.image_to_data`
  with TSV fallback to `tesseract --psm 6 tsv`.
- `tests/test_capture.py`, `tests/test_ocr.py` — assert non-empty box list on a known fixture.

### Milestone 2: Element detection + numbering
- `terminal_master/detect.py` — `detect_buttons(boxes) -> list[NumberedElement]`.
  - Filter to boxes that look interactive (have text, reasonable size, not full-width
    background noise). Heuristic: width < 0.6×image_width AND height in [12,120]px AND
    conf > 40 AND text matches `[A-Za-z0-9]`-ish (button-like).
  - Sort by `top` ascending (top→bottom); assign `number = i+1`.
  - Include `center_x`, `center_y` for click injection.
- `tests/test_detect.py` — fixture with 3 stacked buttons → numbers 1,2,3 top→bottom.

### Milestone 3: Input injection
- `terminal_master/input.py` — `click(element)`, `press_key(seq)`.
  - Use `ydotool click 0xC0` at element center (or `type`/`key` for keyboard).
  - Wrapper: if `/tmp/.ydotool_socket` absent → `sudo ydotool ...` (passwordless sudo).
    Log which path was used.
- `tests/test_input.py` — mock subprocess; assert correct args; no real click in CI.

### Milestone 4: Engine + Telegram-agent bridge contract
- `terminal_master/engine.py`:
  - `run_once() -> list[NumberedElement]` (capture→ocr→detect→return).
  - `act(number) -> bool` (lookup element by number, inject click).
  - `session_loop()` generator yielding lists and awaiting a number (agent feeds it).
- Document the exact API the Telegram agent calls. No Telegram code inside the engine.

### Milestone 5: Repo hygiene + plan delivery
- Add CI? (optional) — `pytest` on push.
- Email the plan to `ewiebotha@gmail.com` via `himalaya` (handled by agent, not engine).

---

## Data Flow

```
Screen ──grim──► PNG ──tesseract──► Boxes(left,top,w,h,text,conf)
                                      │
                                      ▼
                            detect_buttons()  (filter + sort top→bottom)
                                      │
                                      ▼
                       NumberedElement[1..N]  (center_x, center_y)
                                      │
        ┌─────────────────────────────┴───────────────────────────┐
        │  Telegram agent shows list to user                       │
        │  User picks 3  ──► agent calls Engine.act(3)             │
        ▼                                                          │
   ydotool click @ element[3].center  ──► UI changes              │
        │                                                          │
        └──────────────► Engine.run_once() again (loop) ◄─────────┘
```

---

## Risk Table

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| `ydotool` has no socket / needs root | High | High | Wrapper detects missing `/tmp/.ydotool_socket`, falls back to `sudo ydotool` (passwordless sudo confirmed). Document `ydotoold` systemd unit as the clean fix. |
| OCR mislabels non-buttons (window title, body text) | Medium | Medium | Heuristic filter (width/height/conf/text); expose `--strict` flag; allow agent to show raw boxes for correction. |
| Wayland vs X11 capture mismatch | Low | Medium | `capture.py` probes `WAYLAND_DISPLAY`; use `grim` on Wayland, `scrot`/`import` on X11. |
| Number drift between screenshot and click (screen changed) | Medium | Medium | Re-run `run_once()` before each `act()` in tight loops; agent re-confirms list per turn. |
| Screenshot service already broken in Hermes (`screenshot_service.py` crash loop) | n/a | n/a | Terminal_Master uses `grim` directly; does NOT depend on the broken D-Bus service. |

---

## Bite-Sized Tasks (per module)

### Task 1: capture.py
- **Files:** Create `terminal_master/capture.py`, `tests/test_capture.py`
- **Step 1:** Write `capture(output_dir="screenshots") -> str` that runs `grim` and returns PNG path.
- **Step 2:** Test asserts file exists and is a valid PNG (Pillow can open it).
- **Step 3:** Commit.

### Task 2: ocr.py
- **Files:** Create `terminal_master/ocr.py`, `tests/test_ocr.py`
- **Step 1:** Write `ocr_boxes(path) -> list[dict]` using `pytesseract.image_to_data(..., output_type=TSV)`; fallback to `subprocess tesseract --psm 6 tsv` if import fails.
- **Step 2:** Test with `/tmp/ocr_test.png` (known "hello world") → ≥1 box with text.
- **Step 3:** Commit.

### Task 3: detect.py
- **Files:** Create `terminal_master/detect.py`, `tests/test_detect.py`
- **Step 1:** Write `detect_buttons(boxes, img_w, img_h) -> list[NumberedElement]` with filter + top→bottom sort + numbering.
- **Step 2:** Fixture 3 stacked boxes → numbers 1,2,3 in correct order.
- **Step 3:** Commit.

### Task 4: input.py
- **Files:** Create `terminal_master/input.py`, `tests/test_input.py`
- **Step 1:** Write `click(el)` using `ydotool`; socket-detect + sudo fallback.
- **Step 2:** Mock subprocess; assert args; no real click.
- **Step 3:** Commit.

### Task 5: engine.py
- **Files:** Create `terminal_master/engine.py`
- **Step 1:** `run_once()`, `act(n)`, `session_loop()` generator.
- **Step 2:** Docstring contract for the Telegram agent.
- **Step 3:** Commit.

### Task 6: Repo + delivery
- **Files:** `README.md`, `requirements.txt`, `.gitignore`, this plan.
- **Step 1:** Commit all, push to `origin/main`.
- **Step 2:** Agent emails plan to `ewiebotha@gmail.com` via himalaya.

---

## Verify Claims Against Live Source
- `grim` present and working → confirmed `/usr/bin/grim`.
- `tesseract` TSV bbox → confirmed emits `left/top/width/height/text/conf`.
- `ydotool` root/socket behavior → confirmed binary present; socket absent → sudo path required.
- No CSS/visual claims in this plan (engine is headless); N/A for the CSS second-pass rule.

## Execution Handoff
Plan complete and saved to `docs/plans/2026-08-06-terminal-master.md`. Two execution options:
1. **Subagent-Driven (this session)** — I dispatch a fresh subagent per task, review between tasks.
2. **Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints.

Which approach? (Or say "implement" to start now.)
