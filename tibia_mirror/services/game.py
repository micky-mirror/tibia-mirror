"""The Tibia window the app mirrors: which window it is and where its client area is."""

from __future__ import annotations

from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.winapi import win32
from tibia_mirror.winapi.tibia import find_tibia_window


class Game:
    def __init__(self) -> None:
        self.hwnd: Hwnd | None = None  # Tibia's window, None while it is not running
        self.client: Rect | None = None  # its client area on screen, as last seen

    def read_client(self) -> Rect | None:
        """The client area now, or None while it has none (Tibia minimized or gone)."""
        if self.hwnd is None or win32.is_minimized(self.hwnd):
            return None
        client = win32.client_rect(self.hwnd)
        return client if client.w > 0 and client.h > 0 else None

    def current_client(self) -> Rect | None:
        """The client area: read fresh, or as last seen while Tibia is minimized."""
        client = self.read_client()
        if client is not None:
            self.client = client
        return self.client

    def track_client(self) -> tuple[Rect, bool] | None:
        """Read the client area again, and remember it if it changed.

        Return None when there is nothing to do:
        - the client area is the same as before, or
        - there is no client area now (Tibia is not running, or it is minimized).

        If it changed, return two values:
        - the new client area
        - True if the size changed, False if the window only moved
        """
        old, client = self.client, self.read_client()
        if client is None or client == old:
            return None
        self.client = client
        resized = old is not None and (client.w, client.h) != (old.w, old.h)
        return client, resized

    def find(self) -> Hwnd | None:
        """Return Tibia's window, or None if Tibia is not running.

        If the window is not known yet, look for it now and remember it.
        """
        if self.hwnd is None:
            self.hwnd = find_tibia_window()
        return self.hwnd

    def check_closed(self) -> bool:
        """Return True one time, when Tibia has just closed, and forget its window.

        There are three cases:
        - Tibia was never found (hwnd is None): return False. Nothing was open, so nothing closed.
        - Tibia is running: return False.
        - Tibia was running and its window is gone: forget the window and return True.

        After True, hwnd is None again. So the next call returns False,
        and find() starts to look for Tibia again.
        """
        if self.hwnd is None or win32.is_window(self.hwnd):
            return False
        self.hwnd = None
        self.client = None
        return True

    def state(self) -> str:
        """Return what the panel shows about Tibia: "waiting", "minimized" or "connected".

        - "waiting": Tibia is not found yet.
        - "minimized": Tibia is found, but its client area was never seen,
          because it has been minimized since it was found.
        - "connected": Tibia is found and its client area is known.
        """
        if self.hwnd is None:
            return "waiting"
        if self.client is None:
            return "minimized"
        return "connected"

    def title(self) -> str:
        """Return the title of Tibia's window, or "" if Tibia is not running."""
        return win32.window_title(self.hwnd) if self.hwnd is not None else ""

    def is_minimized(self) -> bool:
        """Return True if Tibia is running and its window is minimized now."""
        return self.hwnd is not None and win32.is_minimized(self.hwnd)
