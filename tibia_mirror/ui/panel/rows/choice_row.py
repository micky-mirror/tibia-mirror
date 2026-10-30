"""A row of a card with a few options to choose from, such as the language."""

import tkinter as tk
from collections.abc import Callable, Sequence

from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.segmented_control import SegmentedControl
from tibia_mirror.ui.panel.rows.row import ROW_PAD, SIDE_PAD, draw_label


class ChoiceRow:
    """One setting with a few options to choose from."""

    def __init__(
        self,
        label: str,
        options: Sequence[tuple[str, str]],
        selected: str,
        on_change: Callable[[str], None],
    ) -> None:
        self._label = label
        self._options = options  # (key, text) of each option, from left to right
        self._selected = selected  # the key of the option chosen at the start; the control keeps it
        self._on_change = on_change  # called with the key of the option the user chose

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        row_end_y = label_end_y + px(ROW_PAD)
        self._draw_options(canvas, row_start_y, row_end_y, width)
        return row_end_y

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Pass the pointer on to the options. Return True when a click here would choose one."""
        return self._segmented_control.pointer_moved(position_x, position_y)

    def pointer_left(self) -> None:
        self._segmented_control.pointer_left()

    def set_selected(self, option: str) -> None:
        """Make `option` the chosen one, without reporting it."""
        self._segmented_control.set_selected(option)

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        self._segmented_control.pointer_pressed(position_x, position_y)

    def pointer_released(self, position_x: int, position_y: int) -> None:
        self._segmented_control.pointer_released(position_x, position_y)

    def _draw_options(
        self, canvas: tk.Canvas, row_start_y: int, row_end_y: int, width: int
    ) -> None:
        """The options side by side, at the right, in the middle of the row's height."""
        position_x = width - px(SIDE_PAD)  # the right end of the options
        position_y = (row_start_y + row_end_y) // 2  # the middle of the options

        self._segmented_control = SegmentedControl(
            canvas,
            position_x,
            position_y,
            self._options,
            self._selected,
            self._on_change,
        )
