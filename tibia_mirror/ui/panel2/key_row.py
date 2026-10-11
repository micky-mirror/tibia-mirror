"""A row of a card where the user sets a key, such as the key that hides all mirrors."""

import tkinter as tk

from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.row import ROW_PAD, SIDE_PAD, draw_hint, draw_label


class KeyRow:
    """One setting that is a key or a few keys together, such as Ctrl+H.

    The field for the key is a widget of its own. It hears the mouse and the
    keyboard by itself, so the pointer methods of the row have nothing to do.
    """

    def __init__(self, label: str, hint: str) -> None:
        self._label = label
        self._hint = hint  # the help text under the label

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        hint_width = width - 2 * px(SIDE_PAD)  # as wide as the content of the row
        hint_end_y = draw_hint(canvas, label_end_y, self._hint, hint_width)
        return hint_end_y + px(ROW_PAD)

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Nothing to do: the field for the key hears the pointer by itself."""
        return False

    def pointer_left(self) -> None:
        """Nothing to do: the field for the key hears the pointer by itself."""

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Nothing to do: the field for the key hears the pointer by itself."""

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Nothing to do: the field for the key hears the pointer by itself."""
