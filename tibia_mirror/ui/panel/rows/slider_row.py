"""A row of a card with a slider that sets a number, such as an opacity."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.slider import KNOB_SIZE, Slider
from tibia_mirror.ui.panel.rows.row import ROW_PAD, SIDE_PAD, draw_hint, draw_label

# Sizes at 100% display scaling; px() scales them where they are used.
SLIDER_GAP = 16  # from the end of the help text to the middle line of the slider


class SliderRow:
    """One setting that is a number, set with a slider."""

    def __init__(
        self,
        label: str,
        hint: str,
        *,
        value: float,
        start: float,
        end: float,
        step: float,
        lowest: float,
        value_text: Callable[[float], str],
        on_change: Callable[[float], None],
    ) -> None:
        self._label = label
        self._hint = hint  # the help text under the label
        self._value = value  # the value the slider starts at; the slider keeps it after that
        self._start = start  # the value at the left end of the slider
        self._end = end  # the value at the right end of the slider
        self._step = step  # the knob moves in steps of this size
        self._lowest = lowest  # the knob does not go below this value
        self._value_text = value_text  # makes the text that shows a value, such as "50%"
        self._on_change = on_change  # called with the new value each time the knob moves a step

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        self._draw_value(canvas, row_start_y, width)
        hint_width = width - 2 * px(SIDE_PAD)  # as wide as the content of the row
        hint_end_y = draw_hint(canvas, label_end_y, self._hint, hint_width)
        slider_end_y = self._draw_slider(canvas, hint_end_y, width)
        return slider_end_y + px(ROW_PAD)

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Pass the pointer on to the slider. Return True when a press here would move the knob."""
        return self._slider.pointer_moved(position_x, position_y)

    def pointer_left(self) -> None:
        self._slider.pointer_left()

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        self._slider.pointer_pressed(position_x, position_y)

    def pointer_released(self, position_x: int, position_y: int) -> None:
        self._slider.pointer_released()

    def _draw_value(self, canvas: tk.Canvas, row_start_y: int, width: int) -> None:
        """The value as text, at the right, on the same line as the label."""
        # both are kept to change the text when the value changes
        self._canvas = canvas
        self._value_item = canvas.create_text(
            width - px(SIDE_PAD),
            row_start_y + px(ROW_PAD),
            text=self._value_text(self._value),
            anchor="ne",
            font=theme.FONT,
            fill=theme.SUBTEXT,
        )

    def _draw_slider(self, canvas: tk.Canvas, hint_end_y: int, width: int) -> int:
        """The slider under the help text, as wide as the content of the row.

        Return the y where the slider ends.
        """
        position_y = hint_end_y + px(SLIDER_GAP)  # the middle line of the slider
        self._slider = Slider(
            canvas,
            px(SIDE_PAD),
            width - px(SIDE_PAD),
            position_y,
            self._value,
            start=self._start,
            end=self._end,
            step=self._step,
            lowest=self._lowest,
            on_change=self._on_value_changed,
        )
        # the knob is the highest part of the slider, and half of it is under the middle line
        return position_y + px(KNOB_SIZE) // 2

    def _on_value_changed(self, value: float) -> None:
        """Show the new value as text, and report it."""
        self._canvas.itemconfigure(self._value_item, text=self._value_text(value))
        self._on_change(value)
