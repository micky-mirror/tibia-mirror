"""A row of a card with a dropdown to choose one option from a list."""

import tkinter as tk
from collections.abc import Callable, Sequence

from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.row import ROW_PAD, draw_label


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
        return label_end_y + px(ROW_PAD)

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Nothing to do: the picker hears the pointer by itself."""
        return False

    def pointer_left(self) -> None:
        """Nothing to do: the picker hears the pointer by itself."""

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Nothing to do: the picker hears the pointer by itself."""

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Nothing to do: the picker hears the pointer by itself."""
