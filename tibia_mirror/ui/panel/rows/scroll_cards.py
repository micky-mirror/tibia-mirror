"""A scrolling column of cards, each under its own caption."""

import tkinter as tk
from collections.abc import Sequence

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.widgets import ScrollList
from tibia_mirror.ui.panel.rows.row import Row
from tibia_mirror.ui.panel.rows.row_card import RowCard

# Sizes at 100% display scaling; px() scales them where they are used.
TOP_PAD = 8  # above the first caption
BOTTOM_PAD = 8  # below the last card
CAPTION_TOP_PAD = 10  # above each caption
CAPTION_BOTTOM_PAD = 6  # between a caption and its card


class ScrollCards(tk.Frame):
    """A column of cards, each under its own caption.

    It scrolls when the window is too short to show all of it.
    """

    def __init__(self, parent: tk.Misc, width: int, side_pad: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width  # the width of the cards, in pixels
        self._add_column(side_pad)

    def add_caption(self, text: str) -> None:
        """Add the small grey title of a group, under what is already there."""
        caption = tk.Label(
            self._column,
            text=text,
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT_CAPTION,
        )
        caption.pack(
            side="top",
            anchor="w",
            pady=(px(CAPTION_TOP_PAD), px(CAPTION_BOTTOM_PAD)),
        )

    def add_card(self, rows: Sequence[Row]) -> None:
        """Add a rounded box with the rows of one group, under what is already there."""
        card = RowCard(self._column, self._width, rows)
        card.pack(side="top", anchor="w")

    def _add_column(self, side_pad: int) -> None:
        """The column that holds the captions and the cards, one under another."""
        scroll_list = ScrollList(self, width=self._width)
        scroll_list.pack(
            side="top",
            anchor="w",
            fill="y",
            expand=True,
            padx=(side_pad, 0),
            pady=(px(TOP_PAD), px(BOTTOM_PAD)),
        )
        self._column = scroll_list.inner
