"""The window of Tibia."""

from dataclasses import dataclass

from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.handles import Hwnd


@dataclass(frozen=True)
class GameWindow:
    handle: Hwnd  # the number Windows knows the window by
    client_area: Rect  # the inside of the window, where the game is drawn, on the screen
    is_minimized: bool
    is_in_front: bool
