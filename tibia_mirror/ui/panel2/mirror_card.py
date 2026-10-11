"""The card of one mirror on the Mirrors page."""

import tkinter as tk

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.mirror_info import MirrorInfo

# Sizes at 100% display scaling; px() scales them where they are used.
HEIGHT = 62
RADIUS = 8  # of the rounded corners


class MirrorCard(tk.Canvas):
    """The card of one mirror: its name and size, its buttons and its opacity slider."""

    def __init__(self, parent: tk.Misc, width: int, mirror: MirrorInfo) -> None:
        # No focus ring and no border: Tk adds both to a canvas.
        super().__init__(
            parent,
            width=width,
            height=px(HEIGHT),
            bg=theme.BG,
            highlightthickness=0,
            bd=0,
        )
        self._width = width
        self._mirror = mirror  # what the card shows
        self._draw_background()

    def _draw_background(self) -> None:
        """The rounded shape of the card, a little lighter than the page."""
        self._background = rounded_image(
            self,
            width=self._width,
            height=px(HEIGHT),
            radius=px(RADIUS),
            colour=theme.SURFACE,
            background=theme.BG,
        )
        self.create_image(0, 0, anchor="nw", image=self._background)
