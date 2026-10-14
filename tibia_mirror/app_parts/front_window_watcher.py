"""The window the user works in."""

import os
import tkinter as tk
from collections.abc import Callable

from tibia_mirror.config import FRONT_WINDOW_POLL_MS
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.winapi import win32

# Windows that come to the front for a moment while the user switches windows
# (taskbar, Alt+Tab). They do not count as the window the user works in.
EXCLUDED_WINDOWS = frozenset(
    {
        "Shell_TrayWnd",
        "Shell_SecondaryTrayWnd",
        "MultitaskingViewFrame",
        "XamlExplorerHostIslandWindow",
        "TaskSwitcherWnd",
        "ForegroundStaging",
    }
)


class FrontWindowWatcher:
    """Knows the last window in front, not counting the app's own windows."""

    def __init__(self, window: tk.Misc, on_changed: Callable[[], None]) -> None:
        self._window = window
        self._on_changed = on_changed
        self._last_front_window: Hwnd | None = None

        self._remember_front_window()
        self._check_on_delay()

    @property
    def last_front_window(self) -> Hwnd | None:
        """The last window in front that is not ignored. None until there was one."""
        return self._last_front_window

    def _remember_front_window(self) -> None:
        """Remember the window in front, unless it is ignored."""
        front_window = win32.foreground_window()

        if front_window is None or self._is_ignored(front_window):
            return

        self._last_front_window = front_window

    def _is_ignored(self, front_window: Hwnd) -> bool:
        is_same_process: bool = win32.window_process_id(front_window) == os.getpid()
        is_excluded: bool = win32.window_class(front_window) in EXCLUDED_WINDOWS

        return is_same_process or is_excluded

    def _check_on_delay(self) -> None:
        """Plan the next check."""
        self._window.after(FRONT_WINDOW_POLL_MS, self._check)

    def _check(self) -> None:
        """Look at the window in front again, and tell the app if it changed."""
        # plan the next check first, so an error in this one cannot stop the checks
        self._check_on_delay()

        previous_front_window = self._last_front_window
        self._remember_front_window()

        if self._last_front_window != previous_front_window:
            self._on_changed()
