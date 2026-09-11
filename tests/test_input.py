"""Tests for input.py — mock subprocess; assert correct ydotool args; no real click."""
from unittest import mock

import pytest

from terminal_master.detect import NumberedElement
from terminal_master.input import click, press_key, type_text


def _el() -> NumberedElement:
    return NumberedElement(
        number=1, text="OK", left=10, top=20, width=80, height=30, center_x=50, center_y=35
    )


def _fake_run(returncode=0):
    m = mock.Mock()
    m.returncode = returncode
    m.stderr = ""
    return m


def test_click_uses_daemon_socket_when_present():
    el = _el()
    with mock.patch("terminal_master.input.os.path.exists", return_value=True), mock.patch(
        "terminal_master.input.subprocess.run", return_value=_fake_run()
    ) as run:
        assert click(el) is True
    cmds = [c.args for c in run.call_args_list]
    assert cmds[0][0] == ["ydotool", "mousemove", "-x", "50", "-y", "35"]
    assert cmds[1][0] == ["ydotool", "click", "0xC0"]


def test_click_falls_back_to_sudo_when_socket_absent():
    el = _el()
    with mock.patch("terminal_master.input.os.path.exists", return_value=False), mock.patch(
        "terminal_master.input.subprocess.run", return_value=_fake_run()
    ) as run:
        assert click(el) is True
    cmds = [c.args for c in run.call_args_list]
    assert cmds[0][0] == ["sudo", "-n", "ydotool", "mousemove", "-x", "50", "-y", "35"]
    assert cmds[1][0] == ["sudo", "-n", "ydotool", "click", "0xC0"]


def test_click_raises_on_failure():
    el = _el()
    with mock.patch("terminal_master.input.os.path.exists", return_value=True), mock.patch(
        "terminal_master.input.subprocess.run", return_value=_fake_run(returncode=1)
    ):
        with pytest.raises(RuntimeError):
            click(el)


def test_press_key_uses_prefix():
    with mock.patch("terminal_master.input.os.path.exists", return_value=True), mock.patch(
        "terminal_master.input.subprocess.run", return_value=_fake_run()
    ) as run:
        assert press_key("24:1 24:0") is True
    assert run.call_args.args[0] == ["ydotool", "key", "24:1 24:0"]


def test_type_text_uses_prefix():
    with mock.patch("terminal_master.input.os.path.exists", return_value=False), mock.patch(
        "terminal_master.input.subprocess.run", return_value=_fake_run()
    ) as run:
        assert type_text("hello") is True
    assert run.call_args.args[0] == ["sudo", "-n", "ydotool", "type", "hello"]
