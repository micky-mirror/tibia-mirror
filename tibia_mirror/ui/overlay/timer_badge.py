"""The badge under a mirror that shows the time of its timer."""

import tkinter as tk
import tkinter.font as tkfont

from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.windows import keep_open
from tibia_mirror.winapi import dwm, win32

# It sits over the game, not the panel, so its colours are the same in both themes.
BADGE_BG = "#11111b"
IDLE_TEXT = "#a6adc8"  # before the timer starts, and while it is paused
RUNNING_TEXT = "#ffffff"
DONE_TEXT = "#f38ba8"  # from the alert time on
FONT = ("Segoe UI Semibold", 9)  # all digits of Segoe UI have the same width


class TimerBadge(tk.Toplevel):
    """A small dark pill just under the bottom-right corner of a mirror."""

    # sizes at 100% display scaling
    PAD_X, PAD_Y = 6, 1
    GAP = 3  # between the frame of the mirror and the badge
    RADIUS = 5

    def __init__(self, parent: tk.Misc) -> None:
        super().__init__(parent, bg=BADGE_BG)
        self.withdraw()  # hidden until the mirror shows it
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        # only the app closes a mirror
        keep_open(self)
        # Tk deletes the font when no Python object holds it
        self._font = tkfont.Font(font=FONT)
        self._width, self._height = self._get_size()
        self._label = self._create_label()
        # the number Windows knows this window by
        self._window_handle: Hwnd = win32.toplevel_hwnd(self)
        # window layer setup: always fully visible, also on a see-through mirror
        win32.set_alpha(self._window_handle, 1.0)
        win32.set_click_through(self._window_handle, True)
        self._set_rounded_shape()

    def show(self, picture_area: Rect, border: int) -> None:
        """Show the badge under the picture, in line with the right edge of its frame."""
        frame_area = picture_area.grown(border)
        left = frame_area.x + frame_area.w - self._width
        top = frame_area.y + frame_area.h + px(self.GAP)
        self.geometry(f"+{left}+{top}")
        self.deiconify()
        self.attributes("-topmost", True)  # above other windows, also above the game

    def set_text(self, text: str, colour: str) -> None:
        """Show this time on the badge, in this colour."""
        self._label.configure(text=text, fg=colour)

    def _get_size(self) -> tuple[int, int]:
        """The size that fits the longest time, so the badge never changes size."""
        width = self._font.measure("00:00") + 2 * px(self.PAD_X)
        height = self._font.metrics("linespace") + 2 * px(self.PAD_Y)

        return width, height

    def _create_label(self) -> tk.Label:
        """The time, in the middle of the badge."""
        label = tk.Label(self, bg=BADGE_BG, fg=IDLE_TEXT, font=self._font, padx=0, pady=0)
        label.place(relx=0.5, rely=0.5, anchor="center")

        return label

    def _set_rounded_shape(self) -> None:
        """Give the window its size and cut it into a pill with rounded corners.

        It is our own shape, because the rounding of Windows adds a shadow.
        """
        self.geometry(f"{self._width}x{self._height}")
        self.update_idletasks()  # take the size before the shape is cut
        dwm.set_rounded_corners(self._window_handle, False)
        win32.set_ring_shape(self._window_handle, self._width, self._height, px(self.RADIUS), None)
