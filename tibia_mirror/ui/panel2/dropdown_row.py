"""A row of a card with a dropdown to choose one option from a list."""

import tkinter as tk
from collections.abc import Callable, Sequence

from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.dropdown_picker import DropdownPicker
from tibia_mirror.ui.panel2.row import ROW_PAD, SIDE_PAD, draw_label


class DropdownRow:
    """One setting with a list of options to choose from.

    The picker is a widget of its own. It hears the mouse by itself, so the
    pointer methods of the row have nothing to do.
    """

    def __init__(
        self,
        label: str,
        options: Sequence[tuple[str, str]],
        selected: str,
        on_change: Callable[[str], None],
    ) -> None:
        self._label = label
        self._options = options  # (key, text) of each option, from top to bottom
        self._selected = selected  # the key of the chosen option
        self._on_change = on_change  # called with the key of the option the user chose

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        row_end_y = label_end_y + px(ROW_PAD)
        self._add_picker(canvas, row_start_y, row_end_y, width)
        return row_end_y

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Nothing to do: the picker hears the pointer by itself."""
        return False

    def pointer_left(self) -> None:
        """Nothing to do: the picker hears the pointer by itself."""

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Nothing to do: the picker hears the pointer by itself."""

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Nothing to do: the picker hears the pointer by itself."""

    def _add_picker(self, canvas: tk.Canvas, row_start_y: int, row_end_y: int, width: int) -> None:
        """The picker at the right, in the middle of the row's height."""
        picker = DropdownPicker(canvas, self._options, self._selected, self._on_change)
        position_x = width - px(SIDE_PAD)  # the right end of the picker
        position_y = (row_start_y + row_end_y) // 2  # the middle of the picker

        canvas.create_window(position_x, position_y, window=picker, anchor="e")
