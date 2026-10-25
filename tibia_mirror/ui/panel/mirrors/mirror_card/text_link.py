"""A text that works like a link, drawn on a canvas that something else owns."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.core.geometry import Box
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.tooltip import Tooltip
from tibia_mirror.ui.panel.mirrors.mirror_card.tip import Tip


class TextLink:
    """A grey text that works like a link.

    While the pointer is over it, it is in the accent colour.
    """

    # Sizes at 100% display scaling; px() scales them where they are used.
    SLACK_X = 3  # the link also reacts this far to the left and right of its text
    SLACK_Y = 2  # and this far above and below it

    def __init__(
        self,
        canvas: tk.Canvas,
        position_x: int,
        middle_y: int,
        text: str,
        tip: Tip,
        on_click: Callable[[], None],
    ) -> None:
        self._canvas = canvas
        self._position_x = position_x  # where the text starts
        self._middle_y = middle_y
        self._text = text
        self._tip = tip  # the hint that opens while the pointer rests on the link
        self._tooltip = Tooltip(canvas.winfo_toplevel())
        self._on_click = on_click  # what the link does when it is clicked
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
        self._update_look()
        self._update_tip()

    def click(self) -> None:
        """Do what the link is for."""
        self._on_click()

    def _update_look(self) -> None:
        """The text in the accent colour while hovered, in grey when not."""
        colour = theme.ACCENT if self._is_hovered else theme.SUBTEXT

        self._canvas.itemconfigure(self._text_item, fill=colour)

    def _update_tip(self) -> None:
        """Open the hint while the link is hovered, and close it when it is not."""
        if self._is_hovered:
            self._tooltip.show(self._tip.title, self._get_screen_box(), self._tip.detail)
        else:
            self._tooltip.hide()

    def _get_screen_box(self) -> Box:
        """The place of the text on the screen. The hint opens under it."""
        left, top, right, bottom = self._canvas.bbox(self._text_item)
        canvas_x = self._canvas.winfo_rootx()
        canvas_y = self._canvas.winfo_rooty()
        return (canvas_x + left, canvas_y + top, canvas_x + right, canvas_y + bottom)

    def _draw_text(self) -> None:
        self._text_item = self._canvas.create_text(
            self._position_x,
            self._middle_y,
            text=self._text,
            anchor="w",
            font=theme.FONT,
            fill=theme.SUBTEXT,
        )
