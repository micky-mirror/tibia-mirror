"""The colour picker: a small window with round colour swatches, under the colour dot."""

from __future__ import annotations

import math
import tkinter as tk
from collections.abc import Callable

from tibia_mirror.core.geometry import Box
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.winapi import dwm, win32

# Sizes at 100% display scaling; px() scales them where they are used.
GAP = 4  # between the colour dot and the picker
PAD = 8  # around the swatches, inside the picker
SWATCH_SIZE = 18  # of one round swatch
SWATCH_GAP = 8  # between two swatches


class ColourPicker(tk.Toplevel):
    """The colours to pick from, as round swatches in rows, in a small window."""

    def __init__(
        self,
        window: tk.Misc,
        colours: dict[str, str],
        selected: str,
        per_row: int,
        on_pick: Callable[[str], None],
    ) -> None:
        super().__init__(window, bg=theme.SURFACE)
        self.withdraw()  # hidden until it has a place
        self._window = window  # the window under the picker; it gets the focus back
        self._colours = colours  # the name and the hex code of each colour, in the order shown
        self._selected = selected  # the name of the chosen colour
        self._per_row = per_row  # how many swatches one row holds
        self._on_pick = on_pick  # called with the name of the colour the user picks
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        self.attributes("-topmost", True)  # above the panel, which can be on top too
        # rounded corners, a shadow and a thin border, all drawn by Windows
        dwm.round_popup(win32.toplevel_hwnd(self), theme.SURFACE_HI)
        # add picker content
        self._add_canvas()
        self._bind_events()

    def open(self, box: Box) -> None:
        """Show the picker under `box`, from its left side. `box` is a place on the screen."""
        left, _top, _right, bottom = box
        position_y = bottom + px(GAP)

        self.geometry(f"+{left}+{position_y}")
        self.deiconify()
        self.grab_set()  # every click of the app comes to the picker
        self.focus_force()  # the Escape key comes to the picker

    def close(self) -> None:
        """Close the picker, and give the focus back to the window under it."""
        self.destroy()
        self._window.focus_force()

    def _add_canvas(self) -> None:
        """The surface the swatches are drawn on. It fills the whole picker."""
        width, height = self._get_size()

        self._canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True)

    def _get_size(self) -> tuple[int, int]:
        """Room for every swatch, with a pad around them."""
        columns = min(self._per_row, len(self._colours))
        rows = math.ceil(len(self._colours) / self._per_row)
        width = 2 * px(PAD) + columns * self._get_step() - px(SWATCH_GAP)
        height = 2 * px(PAD) + rows * self._get_step() - px(SWATCH_GAP)

        return width, height

    def _get_step(self) -> int:
        """From the start of one swatch to the start of the next one."""
        return px(SWATCH_SIZE) + px(SWATCH_GAP)

    def _bind_events(self) -> None:
        self.bind("<Escape>", self._on_escape)
        self.bind("<FocusOut>", self._on_focus_out)
        self.protocol("WM_DELETE_WINDOW", self.close)  # Alt+F4

    def _on_escape(self, event: tk.Event[tk.Misc]) -> None:
        self.close()

    def _on_focus_out(self, event: tk.Event[tk.Misc]) -> None:
        # another app has the focus now, so the picker closes and leaves the focus there
        if event.widget is self:
            self.destroy()
