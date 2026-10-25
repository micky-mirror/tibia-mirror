"""Small hover hints, styled like the rest of the app."""

import time
import tkinter as tk
from dataclasses import dataclass

from tibia_mirror.core.geometry import Box
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.windows import keep_open
from tibia_mirror.winapi import dwm, win32

DELAY_MS = 500
# Moving to another target this soon after a hint closed shows the next at once.
WARM_S = 0.4
# Sizes at 100% display scaling, scaled with px() where used.
GAP = 6
PAD_X, PAD_Y = 8, 5
DETAIL_WIDTH = 230  # the explanation line wraps at this width


@dataclass(frozen=True)
class _Hint:
    """The open hint's window and its two lines."""

    win: tk.Toplevel
    title: tk.Label
    detail: tk.Label


class Tooltip:
    """One hover hint at a time: show(title, box, detail) on enter, hide() on leave.

    The title says what a click does; the optional detail explains it. It opens
    below the target (above near the screen's bottom) and never takes focus.
    """

    def __init__(self, master: tk.Misc) -> None:
        self._master = master
        self._hint: _Hint | None = None
        self._pending: str | None = None
        self._closed_at = float("-inf")

    def show(self, title: str, box: Box, detail: str = "") -> None:
        self._cancel()
        if self._hint is not None or time.monotonic() - self._closed_at < WARM_S:
            self._open(title, detail, box)
        else:
            self._pending = self._master.after(DELAY_MS, lambda: self._open(title, detail, box))

    def hide(self) -> None:
        self._cancel()
        if self._hint is not None:
            self._hint.win.destroy()
            self._hint = None
            self._closed_at = time.monotonic()

    def _cancel(self) -> None:
        if self._pending is not None:
            self._master.after_cancel(self._pending)
            self._pending = None

    def _open(self, title: str, detail: str, box: Box) -> None:
        self._pending = None
        if self._hint is None:
            self._hint = self._build()
        hint = self._hint
        hint.title.config(text=title)
        hint.detail.config(text=detail)
        if detail:
            hint.detail.pack(anchor="w", pady=(px(1), 0))
        else:
            hint.detail.pack_forget()
        self._place(hint.win, box)

    def _build(self) -> _Hint:
        win = tk.Toplevel(self._master, bg=theme.SURFACE_HI)
        keep_open(win)
        win.withdraw()
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        # A 1px SURFACE_HI frame on Windows 10; on 11 Windows draws a rounded border.
        body = tk.Frame(win, bg=theme.CRUST, padx=px(PAD_X), pady=px(PAD_Y))
        body.pack(padx=dwm.POPUP_FRAME, pady=dwm.POPUP_FRAME)
        title = tk.Label(body, bg=theme.CRUST, fg=theme.TEXT, font=theme.FONT_CAPTION)
        title.pack(anchor="w")
        detail = tk.Label(
            body,
            bg=theme.CRUST,
            fg=theme.SUBTEXT,
            font=theme.FONT_SMALL,
            justify="left",
            wraplength=px(DETAIL_WIDTH),
        )
        return _Hint(win, title, detail)

    def _place(self, win: tk.Toplevel, box: Box) -> None:
        x0, y0, x1, y1 = box
        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        center_x = (x0 + x1) // 2
        area = win32.work_area_at((center_x, (y0 + y1) // 2))
        x = min(max(center_x - w // 2, area.x), area.right - w)
        gap = px(GAP)
        y = y1 + gap if y1 + gap + h <= area.bottom else y0 - gap - h
        win.geometry(f"+{x}+{y}")
        win.deiconify()
        dwm.round_popup(win32.toplevel_hwnd(win), theme.SURFACE_HI, small=True)
