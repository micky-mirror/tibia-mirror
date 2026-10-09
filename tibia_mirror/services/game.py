"""The Tibia window the app mirrors: which window it is and where its client area is."""

from __future__ import annotations

from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.handles import Hwnd


class Game:
    def __init__(self) -> None:
        self.hwnd: Hwnd | None = None  # Tibia's window, None while it is not running
        self.client: Rect | None = None  # its client area on screen, as last seen
