"""The input watcher: what it passes on, and when."""

import time

import pytest

from tibia_mirror.app_parts import input_watcher as watcher_module
from tibia_mirror.app_parts.input_watcher import InputWatcher
from tibia_mirror.winapi import win32

SHIFT, LEFT_CTRL, RIGHT_ALT, A, F5 = 0xA0, 0xA2, 0xA5, 0x41, 0x74


class FakeWindow:
    """Stands in for the app window. It only remembers the function that was planned."""

    def __init__(self) -> None:
        self.planned = None  # the function given to after()

    def after(self, delay_ms, function):
        self.planned = function

    def run_planned(self) -> None:
        """Run the planned function, as the real window does when the wait is over."""
        function = self.planned
        self.planned = None
        function()


class FakeRawInputWindow:
    """Stands in for the hidden window. A test calls its two functions, as Windows would."""

    def __init__(self, on_left_down, on_key_change) -> None:
        self.on_left_down = on_left_down
        self.on_key_change = on_key_change


def create_watcher(monkeypatch, on_click, on_key):
    """A watcher on fakes. Returns its raw input window and the app window."""
    raw_input_windows = []

    def create_raw_input_window(on_left_down, on_key_change):
        raw_input_window = FakeRawInputWindow(on_left_down, on_key_change)
        raw_input_windows.append(raw_input_window)
        return raw_input_window

    monkeypatch.setattr(watcher_module, "RawInputWindow", create_raw_input_window)
    monkeypatch.setattr(win32, "cursor_pos", lambda: (120, 340))
    window = FakeWindow()
    InputWatcher(window, on_click, on_key)
    return raw_input_windows[0], window


@pytest.fixture
def watched(monkeypatch):
    """A watcher on fakes: its raw input window, the app window, and what it passed on."""
    passed_on = []
    raw_input_window, window = create_watcher(
        monkeypatch,
        on_click=lambda *args: passed_on.append(("click", *args)),
        on_key=lambda *args: passed_on.append(("key", *args)),
    )
    return raw_input_window, window, passed_on


def press(raw_input_window, *key_codes):
    """Press the keys one after another and keep them down."""
    for key_code in key_codes:
        raw_input_window.on_key_change(key_code, True)


def release(raw_input_window, *key_codes):
    for key_code in key_codes:
        raw_input_window.on_key_change(key_code, False)


def without_times(passed_on):
    return [call[:-1] for call in passed_on]


def test_presses_wait_for_the_timer_and_keep_their_order(watched):
    # Windows calls the raw input window inside Tk's loop, where nothing may be passed on yet.
    raw_input_window, window, passed_on = watched
    press(raw_input_window, A)
    raw_input_window.on_left_down()
    assert passed_on == []

    window.run_planned()
    assert without_times(passed_on) == [("key", A, ()), ("click", 120, 340)]


def test_click_keeps_the_pointer_and_the_time_of_the_press(watched, monkeypatch):
    raw_input_window, window, passed_on = watched
    monkeypatch.setattr(time, "monotonic", lambda: 10.0)
    raw_input_window.on_left_down()
    # the pointer moved and the time went on before the timer passed the click on
    monkeypatch.setattr(win32, "cursor_pos", lambda: (999, 999))
    monkeypatch.setattr(time, "monotonic", lambda: 99.0)
    window.run_planned()

    assert passed_on == [("click", 120, 340, 10.0)]


def test_key_has_the_held_modifiers_and_the_time_of_the_press(watched, monkeypatch):
    raw_input_window, window, passed_on = watched
    monkeypatch.setattr(time, "monotonic", lambda: 10.0)
    press(raw_input_window, LEFT_CTRL, RIGHT_ALT, F5)
    # the time went on before the timer passed the key on
    monkeypatch.setattr(time, "monotonic", lambda: 99.0)
    window.run_planned()

    assert passed_on == [("key", F5, ("ctrl", "alt"), 10.0)]


def test_repeats_and_modifiers_alone_are_not_passed_on(watched):
    raw_input_window, window, passed_on = watched
    press(raw_input_window, SHIFT, A, A)  # the second A is the repeat of a held key
    release(raw_input_window, A, SHIFT)
    press(raw_input_window, A)
    window.run_planned()

    assert without_times(passed_on) == [("key", A, ("shift",)), ("key", A, ())]


def test_the_timer_plans_its_next_run_and_passes_each_press_once(watched):
    raw_input_window, window, passed_on = watched
    press(raw_input_window, A)
    window.run_planned()
    window.run_planned()

    assert without_times(passed_on) == [("key", A, ())]
    assert window.planned is not None


def test_an_error_in_the_app_does_not_stop_the_timer(monkeypatch):
    def fail(*args):
        raise RuntimeError

    raw_input_window, window = create_watcher(monkeypatch, on_click=fail, on_key=fail)
    press(raw_input_window, A)
    with pytest.raises(RuntimeError):
        window.run_planned()

    assert window.planned is not None
