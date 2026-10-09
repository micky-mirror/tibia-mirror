"""Finding the Tibia client window, by its executable path (titles alone can match other apps)."""

from tibia_mirror.core.handles import Hwnd
from tibia_mirror.winapi import win32

TITLE_PREFIX = "Tibia"
EXE_SUFFIX = "\\tibia\\bin\\client.exe"


def is_tibia_client(title: str, exe_path: str) -> bool:
    return title.startswith(TITLE_PREFIX) and exe_path.lower().endswith(EXE_SUFFIX)


def find_tibia_window() -> Hwnd | None:
    """HWND of the Tibia client's main window, or None if it is not running."""
    for hwnd in win32.visible_windows():
        title = win32.window_title(hwnd)
        # Cheap title check first; the process lookup only runs for candidates.
        if title.startswith(TITLE_PREFIX) and is_tibia_client(
            title, win32.process_image_path(hwnd)
        ):
            return hwnd
    return None
