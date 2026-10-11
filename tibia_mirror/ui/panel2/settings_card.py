"""A card on the Settings page: a rounded box that holds the rows of one group."""

import tkinter as tk

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import photo
from tibia_mirror.ui.base.render import ButtonStyle, button_pixels
from tibia_mirror.ui.base.scale import px

# Sizes at 100% display scaling; px() scales them where they are used.
RADIUS = 8  # of the rounded corners
SAMPLE_HEIGHT = 44  # of the empty card; goes away when the card gets its first row


class SettingsCard(tk.Canvas):
    """A rounded box for one group of settings."""

    def __init__(self, parent: tk.Misc, width: int) -> None:
        height = px(SAMPLE_HEIGHT)
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=theme.BG,
            highlightthickness=0,
            bd=0,
        )
        self._draw_background(width, height)

    def _draw_background(self, width: int, height: int) -> None:
        """The rounded shape of the card, a little lighter than the page."""
        style = ButtonStyle(fill=theme.SURFACE, radius=px(RADIUS))
        # Tk shows an image only while Python keeps it, so the card stores it.
        self._background = photo(self, button_pixels(width, height, style, theme.BG))
        self.create_image(0, 0, anchor="nw", image=self._background)
