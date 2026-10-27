"""Small hover hints, styled like the rest of the app."""

import tkinter as tk
from dataclasses import dataclass

from tibia_mirror.core.geometry import Box
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.windows import keep_open
from tibia_mirror.winapi import dwm, win32

DELAY_MS = 500
# Sizes at 100% display scaling, scaled with px() where used.
GAP = 6  # between the thing and its hint
PAD_X = 8  # left and right of the texts, inside the hint
PAD_Y = 5  # above and below the texts
DETAIL_GAP = 1  # between the title and the detail
DETAIL_WIDTH = 230  # the detail line wraps at this width


@dataclass(frozen=True)
class Tip:
    """The texts of one hint."""

    title: str  # what a click does, such as "Lock mirror"
    detail: str = ""  # one more line that explains it; "" for none


class HintWindow(tk.Toplevel):
    """The small window of a hint, with its title and its detail."""

    def __init__(self, window: tk.Misc, tip: Tip) -> None:
        super().__init__(window, bg=theme.CRUST, padx=px(PAD_X), pady=px(PAD_Y))
        self.withdraw()  # hidden until it has a place
        self._tip = tip
        # basic window configuration
        keep_open(self)  # only the app closes a hint
        self.overrideredirect(True)  # no title bar and no borders
        self.attributes("-topmost", True)  # above the panel, which can be on top too
        # small rounded corners, a shadow and a thin border, all drawn by Windows
        dwm.round_popup(win32.toplevel_hwnd(self), theme.SURFACE_HI, small=True)
        # add hint texts
        self._add_title()
        self._add_detail()

    def open(self, box: Box) -> None:
        """Show the hint under `box`, from the middle of it. `box` is a place on the screen."""
        _left, _top, _right, bottom = box
        self.update_idletasks()  # Tk measures the texts, so the hint knows its width
        position_x = self._get_position_x(box)
        position_y = bottom + px(GAP)

        self.geometry(f"+{position_x}+{position_y}")
        self.deiconify()

    def _add_title(self) -> None:
        """What a click does."""
        title = tk.Label(
            self,
            text=self._tip.title,
            bg=theme.CRUST,
            fg=theme.TEXT,
            font=theme.FONT_CAPTION,
        )
        title.pack(anchor="w")

    def _add_detail(self) -> None:
        """The line that explains the title, under it. Only when the tip has one."""
        if not self._tip.detail:
            return

        detail = tk.Label(
            self,
            text=self._tip.detail,
            bg=theme.CRUST,
            fg=theme.SUBTEXT,
            font=theme.FONT_SMALL,
            justify="left",
            wraplength=px(DETAIL_WIDTH),
        )
        detail.pack(anchor="w", pady=(px(DETAIL_GAP), 0))

    def _get_position_x(self, box: Box) -> int:
        """In the middle under `box`, but moved in where it would go past a side of the screen."""
        left, _top, right, bottom = box
        width = self.winfo_reqwidth()
        middle_x = (left + right) // 2
        area = win32.work_area_at((middle_x, bottom))
        centred_x = middle_x - width // 2

        return min(max(centred_x, area.x), area.right - width)


class Tooltip:
    """One hover hint at a time: show(tip, box) on enter, hide() on leave.

    The title says what a click does; the optional detail explains it.
    """

    def __init__(self, master: tk.Misc) -> None:
        self._master = master
        self._hint: HintWindow | None = None
        self._pending: str | None = None

    def show(self, tip: Tip, box: Box) -> None:
        self._cancel()
        if self._hint is not None:
            self._open(tip, box)
        else:
            self._pending = self._master.after(DELAY_MS, lambda: self._open(tip, box))

    def hide(self) -> None:
        self._cancel()
        if self._hint is not None:
            self._hint.destroy()
            self._hint = None

    def _cancel(self) -> None:
        if self._pending is not None:
            self._master.after_cancel(self._pending)
            self._pending = None

    def _open(self, tip: Tip, box: Box) -> None:
        self._pending = None
        self.hide()  # the hint that is open now, if there is one
        self._hint = HintWindow(self._master, tip)
        self._hint.open(box)
