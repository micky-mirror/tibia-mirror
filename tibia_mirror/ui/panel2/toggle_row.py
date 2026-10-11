"""A row of a settings card that turns one thing on or off."""

import tkinter as tk

from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.row import ROW_PAD, draw_label


class ToggleRow:
    """One setting that is on or off."""

    def __init__(self, label: str) -> None:
        self._label = label

    def draw(self, canvas: tk.Canvas, top: int, width: int) -> int:
        """Draw the row on the card, starting at `top`. Return where the row ends."""
        label_bottom = draw_label(canvas, top, self._label)
        return label_bottom + px(ROW_PAD)

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
