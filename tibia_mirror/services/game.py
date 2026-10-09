"""The Tibia window the app mirrors: which window it is and where its client area is."""

from __future__ import annotations

from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.winapi import win32


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
