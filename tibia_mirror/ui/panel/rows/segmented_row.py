"""The base of the rows of a card with a few options side by side, at the right of the label."""

import tkinter as tk
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence

from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.segmented_control import HEIGHT as OPTIONS_HEIGHT
from tibia_mirror.ui.panel.controls.segmented_control import SegmentedControl
from tibia_mirror.ui.panel.rows.row import ROW_PAD, SIDE_PAD


class SegmentedRow(ABC):
    """The base of every row with a segmented control at the right of its label."""

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

    @abstractmethod
    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Pass the pointer on to the options. Return True when a click here would choose one."""
        return self._segmented_control.pointer_moved(position_x, position_y)

    def pointer_left(self) -> None:
        self._segmented_control.pointer_left()

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        self._segmented_control.pointer_pressed(position_x, position_y)

    def pointer_released(self, position_x: int, position_y: int) -> None:
        self._segmented_control.pointer_released(position_x, position_y)

    def _draw_options(
        self, canvas: tk.Canvas, row_start_y: int, label_end_y: int, width: int
    ) -> int:
        """The options side by side, at the right, on the line of the label.

        Return the y where the options end.
        """
        position_x = width - px(SIDE_PAD)  # the right end of the options
        # the middle of the label's line, with the pad above and below it
        position_y = (row_start_y + label_end_y + px(ROW_PAD)) // 2

        self._segmented_control = SegmentedControl(
            canvas,
            position_x,
            position_y,
            self._options,
            self._selected,
            self._on_change,
        )
        return position_y + px(OPTIONS_HEIGHT) // 2
