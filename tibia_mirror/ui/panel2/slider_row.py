"""A row of a card with a slider that sets a number, such as an opacity."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.slider import SliderDrawing
from tibia_mirror.ui.panel2.row import ROW_PAD, SIDE_PAD, draw_hint, draw_label

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
        self._value = value
        self._start = start  # the value at the left end of the slider
        self._end = end  # the value at the right end of the slider
        self._step = step  # the knob moves in steps of this size
        self._lowest = lowest  # the knob does not go below this value
        self._value_text = value_text  # makes the text that shows a value, such as "50%"
        self._on_change = on_change  # called with the new value each time the knob moves a step
        self._is_dragging = False  # True from a press on the slider until the button goes up

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        self._draw_value(canvas, row_start_y, width)
        hint_width = width - 2 * px(SIDE_PAD)  # as wide as the content of the row
        hint_end_y = draw_hint(canvas, label_end_y, self._hint, hint_width)
        slider_end_y = self._draw_slider(canvas, hint_end_y, width)
        return slider_end_y + px(ROW_PAD)

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Move the knob with the pointer while the user drags it.

        With no drag, show the knob as active when the pointer is over the slider.
        Return True when a press at this place would move the knob.
        """
        if self._is_dragging:
            self._move_knob(position_x)
            return True
        is_over_slider: bool = self._slider.contains(position_x, position_y)
        self._slider.set_active(is_over_slider)
        return is_over_slider

    def pointer_left(self) -> None:
        """The pointer went out of the card: the knob is not shown as active."""
        # a drag goes on outside the card, and the knob stays active until it ends
        if not self._is_dragging:
            self._slider.set_active(False)

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Start a drag if the button went down on the slider: the knob jumps to the pointer."""
        if self._slider.contains(position_x, position_y):
            self._is_dragging = True
            self._move_knob(position_x)

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """End the drag."""
        self._is_dragging = False

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
        self._slider = SliderDrawing(
            canvas,
            px(SIDE_PAD),
            width - px(SIDE_PAD),
            position_y,
            self._value,
            lo=self._start,
            hi=self._end,
            step=self._step,
            floor=self._lowest,
        )
        # the knob is the highest part of the slider, and half of it is under the middle line
        return position_y + px(SliderDrawing.KNOB) // 2

    def _move_knob(self, position_x: int) -> None:
        """Put the knob as near to this x as the steps and the lowest value allow.

        Show the new value as text too, and report it. Do nothing when the value did not change.
        """
        value = self._slider.value_at(position_x)
        if value == self._value:
            return

        self._value = value
        self._slider.set_value(value)
        self._canvas.itemconfigure(self._value_item, text=self._value_text(value))
        self._on_change(value)
