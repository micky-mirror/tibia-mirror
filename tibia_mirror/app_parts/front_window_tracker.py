"""The window the user works in."""

import os

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


class FrontWindowTracker:
    """Knows the last window in front, not counting the app's own windows."""

    def __init__(self) -> None:
        self._last_front_window: Hwnd | None = None

    @property
    def last_front_window(self) -> Hwnd | None:
        """The last window in front that is not ignored. None until there was one."""
        return self._last_front_window

    def update(self) -> None:
        """Remember the window in front, unless it is ignored."""
        front_window = win32.foreground_window()

        if front_window is None or self._is_ignored(front_window):
            return

        self._last_front_window = front_window

    def _is_ignored(self, front_window: Hwnd) -> bool:
        is_same_process: bool = win32.window_process_id(front_window) == os.getpid()
        is_excluded: bool = win32.window_class(front_window) in EXCLUDED_WINDOWS

        return is_same_process or is_excluded
