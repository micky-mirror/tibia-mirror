"""The base of the rows of a card with a few options side by side, at the right of the label."""

import tkinter as tk
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence

from tibia_mirror.ui.base import theme
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
        *,
        font: theme.FontSpec = theme.FONT,
    ) -> None:
        self._label = label
        self._options = options  # (key, text) of each option, from left to right
        self._selected = selected  # the key of the option chosen at the start; the control keeps it
        self._on_change = on_change  # called with the key of the option the user chose
        self._font = font  # of the texts of the options

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

    def _draw_label_and_options(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """The label at the left and the options at the right, on one line as tall as the options.

        Return the y where the line ends.
        """
        line_start_y = row_start_y + px(ROW_PAD)
        middle_y = line_start_y + px(OPTIONS_HEIGHT) // 2

        self._draw_label(canvas, middle_y)
        self._draw_options(canvas, middle_y, width)
        return line_start_y + px(OPTIONS_HEIGHT)

    def _draw_label(self, canvas: tk.Canvas, middle_y: int) -> None:
        """The name of the setting at the left, in the middle of the line."""
        canvas.create_text(
            px(SIDE_PAD),
            middle_y,
            text=self._label,
            anchor="w",
            font=theme.FONT,
            fill=theme.TEXT,
        )

    def _draw_options(self, canvas: tk.Canvas, middle_y: int, width: int) -> None:
        """The options side by side, at the right, in the middle of the line."""
        position_x = width - px(SIDE_PAD)  # the right end of the options

        self._segmented_control = SegmentedControl(
            canvas,
            position_x,
            middle_y,
            self._options,
            self._selected,
            self._on_change,
            font=self._font,
        )
