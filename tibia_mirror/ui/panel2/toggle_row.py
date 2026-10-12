"""A row of a card that turns one thing on or off."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.row import ROW_PAD, SIDE_PAD, draw_hint, draw_label
from tibia_mirror.ui.panel2.switch import Switch

# Sizes at 100% display scaling; px() scales them where they are used.
SWITCH_GAP = 20  # between the texts and the switch


class ToggleRow:
    """One setting that is on or off."""

    def __init__(
        self, label: str, hint: str, is_on: bool, on_change: Callable[[bool], None]
    ) -> None:
        self._label = label
        self._hint = hint  # the help text under the label
        self._is_on = is_on
        self._on_change = on_change  # called with the new state when the user turns the row
        self._is_hovered = False  # True while the pointer is in the row
        self._is_pressed = False  # True when the mouse button went down in the row

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        hint_end_y = draw_hint(canvas, label_end_y, self._hint, self._get_hint_width(width))
        row_end_y = hint_end_y + px(ROW_PAD)
        self._draw_switch(canvas, row_start_y, row_end_y, width)
        # remembered to know later if the pointer is in the row
        self._row_start_y = row_start_y
        self._row_end_y = row_end_y
        self._row_width = width
        return row_end_y

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Show the switch as hovered when the pointer is anywhere in the row.

        Return True then: a click at any place in the row turns the setting on or off.
        """
        is_in_row: bool = self._is_in_row(position_x, position_y)
        self._set_hovered(is_in_row)
        return is_in_row

    def pointer_left(self) -> None:
        """The pointer went out of the card: the switch is not hovered."""
        self._set_hovered(False)

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Remember if the mouse button went down in the row."""
        self._is_pressed = self._is_in_row(position_x, position_y)

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Turn the setting on or off if the button went down and up in the row."""
        if self._is_pressed and self._is_in_row(position_x, position_y):
            self._toggle()
        self._is_pressed = False

    def _is_in_row(self, position_x: int, position_y: int) -> bool:
        """True when this place is inside the row."""
        is_in_width: bool = 0 <= position_x < self._row_width
        is_in_height: bool = self._row_start_y <= position_y < self._row_end_y
        return is_in_width and is_in_height

    def _set_hovered(self, is_hovered: bool) -> None:
        """Remember if the row is hovered and draw the switch again, only when it changed."""
        if is_hovered == self._is_hovered:
            return
        self._is_hovered = is_hovered
        self._switch.draw(self._is_on, self._is_hovered)

    def _toggle(self) -> None:
        """Change on to off, or off to on, draw the switch again, and report the new state."""
        self._is_on = not self._is_on
        self._switch.draw(self._is_on, self._is_hovered)
        self._on_change(self._is_on)

    def _draw_switch(self, canvas: tk.Canvas, row_start_y: int, row_end_y: int, width: int) -> None:
        """The switch at the right, in the middle of the row's height."""
        position_x = width - px(SIDE_PAD)  # the right end of the switch
        position_y = (row_start_y + row_end_y) // 2  # the middle of the switch
        self._switch = Switch(canvas, position_x, position_y, self._is_on)

    def _get_hint_width(self, width: int) -> int:
        """The width the help text can take: the row without its side space and the switch."""
        return width - 2 * px(SIDE_PAD) - px(Switch.WIDTH) - px(SWITCH_GAP)
