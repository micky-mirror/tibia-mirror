"""The timer's badge: the time on a small dark pill just below a mirror's bottom-right corner."""

import tkinter as tk
import tkinter.font as tkfont

from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.windows import keep_open
from tibia_mirror.winapi import win32

# It sits over the game, not the panel, so its colours are the same in both themes.
BADGE_BG = "#11111b"
IDLE_TEXT = "#a6adc8"  # before the first start
RUNNING_TEXT = "#ffffff"
DONE_TEXT = "#f38ba8"
FONT = ("Segoe UI Semibold", 9)  # Segoe UI's digits all have the same width, so no jitter


class TimerBadge:
    """The timer's time, in a click-through window of its own, always just below the
    mirror (outside it, so it never covers the game image).
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    PAD_X, PAD_Y = 6, 1
    GAP = 3  # below the mirror's frame
    RADIUS = 5

    def __init__(self, root: tk.Misc) -> None:
        font = tkfont.Font(font=FONT)
        self.width = font.measure("00:00") + 2 * px(self.PAD_X)
        self.height = font.metrics("linespace") + 2 * px(self.PAD_Y)
        self.win = tk.Toplevel(root, bg=BADGE_BG)
        keep_open(self.win)
        self.win.overrideredirect(True)
        self.win.attributes("-alpha", 0.0)
        self.win.attributes("-topmost", True)
        self._label = tk.Label(self.win, bg=BADGE_BG, fg=IDLE_TEXT, font=font, padx=0, pady=0)
        self._label.place(relx=0.5, rely=0.5, anchor="center")
        self._font = font  # Tk fonts must outlive their widgets
        self.win.geometry(f"{self.width}x{self.height}+0+0")
        self.hwnd = win32.toplevel_hwnd(self.win)
        win32.set_alpha(self.hwnd, 0.0)
        win32.set_click_through(self.hwnd, True)
        win32.set_ring_shape(self.hwnd, self.width, self.height, px(self.RADIUS), None)
        self.win.withdraw()
        self._shown = False

    def set_text(self, text: str, state: str) -> None:
        """state: "idle" (not started yet), "running" or "done"."""
        color = {"idle": IDLE_TEXT, "running": RUNNING_TEXT, "done": DONE_TEXT}[state]
        self._label.config(text=text, fg=color)

    def place(self, x: int, y: int, w: int, h: int, border: int) -> None:
        """Put it below the image at (x, y), w x h, whose frame is `border` wide,
        right-aligned with the frame's outer edge."""
        left, top = x + w + border - self.width, y + h + border + px(self.GAP)
        self.win.geometry(f"+{left}+{top}")

    def set_alpha(self, alpha: float) -> None:
        win32.set_alpha(self.hwnd, alpha)

    def show(self, shown: bool) -> None:
        if shown == self._shown:
            return
        self._shown = shown
        if shown:
            self.win.deiconify()
            self.win.attributes("-topmost", True)
        else:
            self.win.withdraw()

    def lift(self) -> None:
        if self._shown:
            self.win.lift()

    def destroy(self) -> None:
        self.win.destroy()
