"""A text that works like a link, drawn on a canvas that something else owns."""

import tkinter as tk

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px


class TextLink:
    """A grey text that works like a link.

    While the pointer is over it, it is in the accent colour.
    """

    # Sizes at 100% display scaling; px() scales them where they are used.
    SLACK_X = 3  # the link also reacts this far to the left and right of its text
    SLACK_Y = 2  # and this far above and below it

    def __init__(self, canvas: tk.Canvas, position_x: int, middle_y: int, text: str) -> None:
        self._canvas = canvas
        self._position_x = position_x  # where the text starts
        self._middle_y = middle_y
        self._text = text
        self._is_hovered = False  # True while the pointer is over the link

        self._draw_text()

    def contains(self, position_x: int, position_y: int) -> bool:
        """True when this place is on the text, or very near to it."""
        left, top, right, bottom = self._canvas.bbox(self._text_item)
        slack_x = px(self.SLACK_X)
        slack_y = px(self.SLACK_Y)

        is_in_width: bool = left - slack_x <= position_x < right + slack_x
        is_in_height: bool = top - slack_y <= position_y < bottom + slack_y
        return is_in_width and is_in_height

    def set_hovered(self, is_hovered: bool) -> None:
        """Show the hover look, or take it away. Do nothing when nothing changed."""
        if is_hovered == self._is_hovered:
            return
        self._is_hovered = is_hovered
        colour = theme.ACCENT if is_hovered else theme.SUBTEXT

        self._canvas.itemconfigure(self._text_item, fill=colour)

    def _draw_text(self) -> None:
        self._text_item = self._canvas.create_text(
            self._position_x,
            self._middle_y,
            text=self._text,
            anchor="w",
            font=theme.FONT,
            fill=theme.SUBTEXT,
        )
