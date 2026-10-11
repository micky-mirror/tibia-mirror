"""A row of a settings card with a slider that sets a number, such as an opacity."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.row import ROW_PAD, SIDE_PAD, draw_hint, draw_label


class SliderRow:
    """One setting that is a number, set with a slider."""

    def __init__(
        self, label: str, hint: str, value: float, value_text: Callable[[float], str]
    ) -> None:
        self._label = label
        self._hint = hint  # the help text under the label
        self._value = value
        self._value_text = value_text  # makes the text that shows a value, such as "50%"

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        self._draw_value(canvas, row_start_y, width)
        hint_width = width - 2 * px(SIDE_PAD)  # as wide as the content of the row
        hint_end_y = draw_hint(canvas, label_end_y, self._hint, hint_width)
        return hint_end_y + px(ROW_PAD)

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Move the knob with the pointer while the user drags it.

        With no drag, show the knob as active when the pointer is over the slider.
        Return True when a press at this place would move the knob.
        """
        return False

    def pointer_left(self) -> None:
        """The pointer went out of the card: the knob is not shown as active."""

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Start a drag if the button went down on the slider: the knob jumps to the pointer."""

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """End the drag."""

    def _draw_value(self, canvas: tk.Canvas, row_start_y: int, width: int) -> None:
        """The value as text, at the right, on the same line as the label."""
        canvas.create_text(
            width - px(SIDE_PAD),
            row_start_y + px(ROW_PAD),
            text=self._value_text(self._value),
            anchor="ne",
            font=theme.FONT,
            fill=theme.SUBTEXT,
        )
