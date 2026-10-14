"""The watcher of the window in front: which window counts, and when it tells the app."""

import os

import pytest

from tibia_mirror.app_parts.front_window_watcher import FrontWindowWatcher
from tibia_mirror.winapi import win32

TIBIA = 100
BROWSER = 200
OWN_PANEL = 300
TASKBAR = 400


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


@pytest.fixture
def screen(monkeypatch):
    """The window in front; a test changes it to set the scene."""
    reported = {"front_window": TIBIA}
    process_ids = {OWN_PANEL: os.getpid()}
    classes = {TASKBAR: "Shell_TrayWnd"}

    monkeypatch.setattr(win32, "foreground_window", lambda: reported["front_window"])
    monkeypatch.setattr(win32, "window_process_id", lambda hwnd: process_ids.get(hwnd, 1))
    monkeypatch.setattr(win32, "window_class", lambda hwnd: classes.get(hwnd, "AppWindow"))
    return reported


def do_nothing() -> None:
    pass


def test_remembers_the_window_in_front_at_the_start(screen):
    watcher = FrontWindowWatcher(FakeWindow(), do_nothing)

    assert watcher.last_front_window == TIBIA


@pytest.mark.parametrize("front_window", [OWN_PANEL, TASKBAR, None])
def test_an_ignored_window_keeps_the_last_one(screen, front_window):
    window = FakeWindow()
    watcher = FrontWindowWatcher(window, do_nothing)

    screen["front_window"] = front_window
    window.run_planned()

    assert watcher.last_front_window == TIBIA


def test_a_new_window_in_front_is_told_to_the_app_one_time(screen):
    window = FakeWindow()
    changes = []
    FrontWindowWatcher(window, lambda: changes.append("changed"))

    screen["front_window"] = BROWSER
    window.run_planned()
    window.run_planned()

    assert changes == ["changed"]


def test_nothing_is_told_while_the_same_window_stays_in_front(screen):
    window = FakeWindow()
    changes = []
    FrontWindowWatcher(window, lambda: changes.append("changed"))

    window.run_planned()

    assert changes == []
