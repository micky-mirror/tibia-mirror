"""The frame window behind a rounded mirror."""

import tkinter as tk

from tibia_mirror.config import ROUND_SMALL_RADIUS
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

    def show(self, picture_area: Rect, border: int, colour: str) -> None:
        """Show the frame around the given picture, in the given frame colour."""
        frame_area = picture_area.grown(border)
        self.configure(bg=theme.frame_color(colour))
        self.geometry(f"{frame_area.w}x{frame_area.h}+{frame_area.x}+{frame_area.y}")
        # move the window first, because a new shape makes Tk forget a move it has not done yet
        self.update_idletasks()
        self._set_ring_shape(picture_area, border)
        self.deiconify()
        self.attributes("-topmost", True)  # above other windows, also above the game

    def _set_ring_shape(self, picture_area: Rect, border: int) -> None:
        """Cut the window into a ring with rounded corners around the picture."""
        inner_radius = round(ROUND_SMALL_RADIUS * win32.dpi_scale(self._window_handle))
        outer_radius = inner_radius + border
        frame_width = picture_area.w + 2 * border
        frame_height = picture_area.h + 2 * border
        hole = (border, border, picture_area.w, picture_area.h, inner_radius)

        win32.set_ring_shape(self._window_handle, frame_width, frame_height, outer_radius, hole)
