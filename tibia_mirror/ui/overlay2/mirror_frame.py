"""The frame window behind a rounded mirror."""

import tkinter as tk

from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.windows import keep_open
from tibia_mirror.winapi import dwm, win32


class MirrorFrame(tk.Toplevel):
    """A window behind the picture of a mirror that shows as its frame."""

    def __init__(self, parent: tk.Misc, opacity: float) -> None:
        super().__init__(parent)
        self.withdraw()  # hidden until the mirror shows it
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        # only the app closes a mirror
        keep_open(self)
        # the number Windows knows this window by
        self._window_handle: Hwnd = win32.toplevel_hwnd(self)
        # window layer setup
        win32.set_alpha(self._window_handle, opacity)
        win32.set_click_through(self._window_handle, True)
        # square, because the rounding of Windows adds a shadow
        dwm.set_rounded_corners(self._window_handle, False)

    def show(self, frame_area: Rect, colour: str) -> None:
        """Show the frame at the given place, in the given frame colour."""
        self.configure(bg=theme.frame_color(colour))
        self.geometry(f"{frame_area.w}x{frame_area.h}+{frame_area.x}+{frame_area.y}")
        self.deiconify()
        self.attributes("-topmost", True)  # above other windows, also above the game
