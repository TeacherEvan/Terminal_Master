"""Tests for engine.py — orchestrates capture→ocr→detect→act with mocks.

No real screen, no real ydotool. Patches the four I/O boundaries so the
orchestration logic (scaling, lookup, session loop) is exercised.
"""
from unittest import mock

import pytest

from terminal_master.detect import NumberedElement
from terminal_master.engine import UPSCALE, act, run_once, session_loop
from terminal_master.ocr import WordBox


def _png(path):
    from PIL import Image  # type: ignore

    Image.new("RGB", (100, 100), "black").save(path)


def _el(number=1, cx=200, cy=300):
    return NumberedElement(
        number=number,
        text="OK",
        left=cx - 40,
        top=cy - 10,
        width=80,
        height=20,
        center_x=cx,
        center_y=cy,
    )


def test_run_once_scales_coordinates_back_to_original():
    # detect returns upscaled coords (UPSCALE× the raw image); run_once must
    # divide them back so ydotool clicks the real screen position.
    raw = "/tmp/_tm_test_run_once.png"
    _png(raw)
    fake_words = [WordBox(text="OK", left=10, top=20, width=80, height=20, conf=90.0)]
    fake_elements = [_el(number=1, cx=200 * UPSCALE, cy=300 * UPSCALE)]

    with mock.patch("terminal_master.engine.capture", return_value=raw), mock.patch(
        "terminal_master.engine.ocr_words", return_value=fake_words
    ), mock.patch(
        "terminal_master.engine.detect_buttons", return_value=fake_elements
    ):
        result = run_once()

    assert len(result) == 1
    assert result[0].center_x == 200
    assert result[0].center_y == 300
    assert result[0].number == 1


def test_act_calls_click_for_matching_number():
    el = _el(number=3, cx=50, cy=60)
    with mock.patch("terminal_master.engine.click", return_value=True) as click_mock:
        assert act(3, [el]) is True
    click_mock.assert_called_once_with(el)


def test_act_raises_for_unknown_number():
    el = _el(number=1)
    with mock.patch("terminal_master.engine.click"), pytest.raises(ValueError, match="No option numbered 99"):
        act(99, [el])


def test_session_loop_yields_then_re_captures():
    raw = "/tmp/_tm_test_session.png"
    _png(raw)
    fake_words = [WordBox(text="OK", left=10, top=20, width=80, height=20, conf=90.0)]
    el1 = _el(number=1, cx=10, cy=10)
    el2 = _el(number=2, cx=20, cy=20)

    call_count = {"n": 0}

    def fake_detect(*a, **kw):
        call_count["n"] += 1
        return [el1] if call_count["n"] == 1 else [el2]

    with mock.patch("terminal_master.engine.capture", return_value=raw), mock.patch(
        "terminal_master.engine.ocr_words", return_value=fake_words
    ), mock.patch(
        "terminal_master.engine.detect_buttons", side_effect=fake_detect
    ), mock.patch(
        "terminal_master.engine.click", return_value=True
    ) as click_mock:
        gen = session_loop()
        first = next(gen)
        assert first == [el1]
        # Agent picks option 1 → click fires, then re-capture yields el2
        second = gen.send(1)
        assert second == [el2]
        click_mock.assert_called_once_with(el1)


def test_session_loop_break_on_none():
    raw = "/tmp/_tm_test_break.png"
    _png(raw)
    fake_words = [WordBox(text="OK", left=10, top=20, width=80, height=20, conf=90.0)]
    with mock.patch("terminal_master.engine.capture", return_value=raw), mock.patch(
        "terminal_master.engine.ocr_words", return_value=fake_words
    ), mock.patch(
        "terminal_master.engine.detect_buttons", return_value=[_el()]
    ), mock.patch("terminal_master.engine.click"):
        gen = session_loop()
        next(gen)
        with pytest.raises(StopIteration):
            gen.send(None)
