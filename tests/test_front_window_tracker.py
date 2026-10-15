"""The tracker of the window in front: which window counts."""

import os

import pytest

from tibia_mirror.app_parts.front_window_tracker import FrontWindowTracker
from tibia_mirror.winapi import win32

TIBIA = 100
BROWSER = 200
OWN_PANEL = 300
TASKBAR = 400


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


def test_there_is_no_window_before_the_first_update(screen):
    tracker = FrontWindowTracker()

    assert tracker.last_front_window is None


def test_update_remembers_the_window_in_front(screen):
    tracker = FrontWindowTracker()

    tracker.update()

    assert tracker.last_front_window == TIBIA


@pytest.mark.parametrize("front_window", [OWN_PANEL, TASKBAR, None])
def test_an_ignored_window_keeps_the_last_one(screen, front_window):
    tracker = FrontWindowTracker()
    tracker.update()

    screen["front_window"] = front_window
    tracker.update()

    assert tracker.last_front_window == TIBIA


def test_a_new_window_in_front_replaces_the_last_one(screen):
    tracker = FrontWindowTracker()
    tracker.update()

    screen["front_window"] = BROWSER
    tracker.update()

    assert tracker.last_front_window == BROWSER
