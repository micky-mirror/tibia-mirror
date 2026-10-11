"""A row of a settings card that turns one thing on or off."""

import tkinter as tk

from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.row import ROW_PAD, SIDE_PAD, draw_hint, draw_label
from tibia_mirror.ui.panel2.switch import Switch

# Sizes at 100% display scaling; px() scales them where they are used.
SWITCH_GAP = 20  # between the texts and the switch


class ToggleRow:
    """One setting that is on or off."""

    def __init__(self, label: str, hint: str, is_on: bool) -> None:
        self._label = label
        self._hint = hint  # the help text under the label
        self._is_on = is_on

    def draw(self, canvas: tk.Canvas, top: int, width: int) -> int:
        """Draw the row on the card, starting at `top`. Return where the row ends."""
        label_bottom = draw_label(canvas, top, self._label)
        hint_bottom = draw_hint(canvas, label_bottom, self._hint, self._hint_width(width))
        bottom = hint_bottom + px(ROW_PAD)
        self._draw_switch(canvas, top, bottom, width)
        return bottom

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Show the switch as hovered when the pointer is anywhere in the row.

        Return True then: a click at any place in the row turns the setting on or off.
        """
        return False

    def pointer_left(self) -> None:
        """The pointer went out of the card: the switch is not hovered."""

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Remember if the mouse button went down in the row."""

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Turn the setting on or off if the button went down and up in the row."""

    def _draw_switch(self, canvas: tk.Canvas, top: int, bottom: int, width: int) -> None:
        """The switch at the right, in the middle of the row's height."""
        position_x = width - px(SIDE_PAD)  # the right end of the switch
        position_y = (top + bottom) // 2  # the middle of the switch
        self._switch = Switch(canvas, position_x, position_y, self._is_on)

    def _hint_width(self, width: int) -> int:
        """The width the help text can take: the row without its side space and the switch."""
        return width - 2 * px(SIDE_PAD) - px(Switch.WIDTH) - px(SWITCH_GAP)
