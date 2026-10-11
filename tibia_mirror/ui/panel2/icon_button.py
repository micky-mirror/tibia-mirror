"""A small button with only an icon, drawn on a canvas that something else owns."""

import tkinter as tk

from tibia_mirror.ui.base import theme


class IconButton:
    """A small square button with only an icon.

    While the pointer is over it, it shows a rounded shape behind the icon.
    """

    # Sizes at 100% display scaling; px() scales them where they are used.
    SIZE = 26  # the button is square, so this is its width and its height

    def __init__(
        self, canvas: tk.Canvas, middle_x: int, middle_y: int, icon: str, font: theme.FontSpec
    ) -> None:
        self._canvas = canvas
        self._icon = canvas.create_text(
            middle_x,
            middle_y,
            text=icon,
            font=font,
            fill=theme.SUBTEXT,
        )
