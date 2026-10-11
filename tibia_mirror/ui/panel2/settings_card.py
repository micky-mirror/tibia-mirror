"""A card on the Settings page: a rounded box that holds the rows of one group."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Sequence

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import photo
from tibia_mirror.ui.base.render import ButtonStyle, button_pixels
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.row import SIDE_PAD, Row

# Sizes at 100% display scaling; px() scales them where they are used.
RADIUS = 8  # of the rounded corners


class SettingsCard(tk.Canvas):
    """A rounded box for one group of settings. It is as high as its rows."""

    def __init__(self, parent: tk.Misc, width: int, rows: Sequence[Row]) -> None:
        super().__init__(
            parent,
            width=width,
            bg=theme.BG,
            highlightthickness=0,
            bd=0,
        )
        self._rows = rows
        height = self._draw_rows(width)
        self._draw_background(width, height)
        self.configure(height=height)
        self._bind_events()

    def _draw_rows(self, width: int) -> int:
        """Draw the rows one under another, with a thin line between them.

        Return the height they take together.
        """
        row_end_y = 0
        for row in self._rows:
            row_start_y = row_end_y  # a row starts where the row above it ended
            is_first: bool = row_start_y == 0
            if not is_first:
                self._draw_line(row_start_y, width)
            row_end_y = row.draw(self, row_start_y, width)
        # the end of the last row is the height of all the rows together
        return row_end_y

    def _draw_line(self, position_y: int, width: int) -> None:
        """A thin line across the card, in the colour of the page.

        It starts and ends where the content of the rows does.
        """
        self.create_line(
            px(SIDE_PAD),
            position_y,
            width - px(SIDE_PAD),
            position_y,
            fill=theme.BG,
            width=px(1),
        )

    def _draw_background(self, width: int, height: int) -> None:
        """The rounded shape of the card, a little lighter than the page."""
        style = ButtonStyle(fill=theme.SURFACE, radius=px(RADIUS))
        # Tk shows an image only while Python keeps it, so the card stores it.
        self._background = photo(self, button_pixels(width, height, style, theme.BG))
        background = self.create_image(0, 0, anchor="nw", image=self._background)
        # The rows are drawn first, so the background must go under them.
        self.tag_lower(background)

    def _bind_events(self) -> None:
        # <Enter> too: the pointer can come in and stop, with no <Motion> after it.
        self.bind("<Enter>", self._on_mouse_move)
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_mouse_move(self, event: tk.Event[tk.Canvas]) -> None:
        """Tell every row where the pointer is. Show a hand over a place that can be clicked."""
        is_clickable: bool = False
        for row in self._rows:
            if row.pointer_moved(event.x, event.y):
                is_clickable = True
        self.configure(cursor="hand2" if is_clickable else "")

    def _on_mouse_leave(self, event: tk.Event[tk.Canvas]) -> None:
        for row in self._rows:
            row.pointer_left()
        self.configure(cursor="")

    def _on_mouse_down(self, event: tk.Event[tk.Canvas]) -> None:
        for row in self._rows:
            row.pointer_pressed(event.x, event.y)

    def _on_mouse_up(self, event: tk.Event[tk.Canvas]) -> None:
        for row in self._rows:
            row.pointer_released(event.x, event.y)
        # A click can change what is under the pointer, so look at that place again.
        self._on_mouse_move(event)
