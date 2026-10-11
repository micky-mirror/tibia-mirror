"""A card on the Settings page: a rounded box that holds the rows of one group."""

import tkinter as tk
from collections.abc import Sequence

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import photo
from tibia_mirror.ui.base.render import ButtonStyle, button_pixels
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.choice_row import ChoiceRow

# Sizes at 100% display scaling; px() scales them where they are used.
RADIUS = 8  # of the rounded corners


class SettingsCard(tk.Canvas):
    """A rounded box for one group of settings. It is as high as its rows."""

    def __init__(self, parent: tk.Misc, width: int, rows: Sequence[ChoiceRow]) -> None:
        super().__init__(
            parent,
            width=width,
            bg=theme.BG,
            highlightthickness=0,
            bd=0,
        )
        height = self._draw_rows(rows)
        self._draw_background(width, height)
        self.configure(height=height)

    def _draw_rows(self, rows: Sequence[ChoiceRow]) -> int:
        """Draw the rows one under another. Return the height they take together."""
        position_y = 0
        for row in rows:
            position_y = row.draw(self, position_y)
        return position_y

    def _draw_background(self, width: int, height: int) -> None:
        """The rounded shape of the card, a little lighter than the page."""
        style = ButtonStyle(fill=theme.SURFACE, radius=px(RADIUS))
        # Tk shows an image only while Python keeps it, so the card stores it.
        self._background = photo(self, button_pixels(width, height, style, theme.BG))
        background = self.create_image(0, 0, anchor="nw", image=self._background)
        # The rows are drawn first, so the background must go under them.
        self.tag_lower(background)
