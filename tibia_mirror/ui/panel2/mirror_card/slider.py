"""The opacity slider of a mirror card, with the opacity as a percent."""

import tkinter as tk
from collections.abc import Callable
from dataclasses import replace

from tibia_mirror.config import MIN_OPACITY, OPACITY_STEP
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import percent
from tibia_mirror.ui.controls.slider import SliderDrawing
from tibia_mirror.ui.panel2.mirror_info import MirrorInfo

# Sizes at 100% display scaling; px() scales them where they are used.
SLIDER_Y = 44  # from the top of the card to the middle line of the slider
SIDE_PAD = 14  # from the sides of the card to the slider and to the percent
PERCENT_ROOM = 48  # kept free between the slider and the right side space, for the percent


class MirrorCardSlider:
    """The second line of a mirror card.

    It has the slider that sets how see-through the mirror is, and the opacity
    as a percent at its right.
    """

    def __init__(
        self,
        canvas: tk.Canvas,
        width: int,
        mirror: MirrorInfo,
        on_changed: Callable[[MirrorInfo], None],
    ) -> None:
        self._canvas = canvas
        self._width = width  # of the card
        self._mirror = mirror
        self._on_changed = on_changed  # gets the new info after the opacity was changed
        self._is_dragging = False  # True from a press on the slider until the button goes up

        self._draw_slider()
        self._draw_percent()

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

    def set_mirror(self, mirror: MirrorInfo) -> None:
        """Keep the new state of the mirror."""
        self._mirror = mirror

    def _draw_slider(self) -> None:
        """The slider, from the left side space of the card to the room of the percent."""
        position_x_start = px(SIDE_PAD)
        position_x_end = self._width - px(SIDE_PAD) - px(PERCENT_ROOM)

        self._slider = SliderDrawing(
            self._canvas,
            position_x_start,
            position_x_end,
            px(SLIDER_Y),
            self._mirror.opacity,
            lo=0.0,
            hi=1.0,
            step=OPACITY_STEP,
            floor=MIN_OPACITY,
        )

    def _draw_percent(self) -> None:
        """The opacity as a percent, at the right of the slider."""
        self._percent = self._canvas.create_text(
            self._width - px(SIDE_PAD),
            px(SLIDER_Y),
            text=percent(self._mirror.opacity),
            anchor="e",
            font=theme.FONT,
            fill=theme.SUBTEXT,
        )

    def _move_knob(self, position_x: int) -> None:
        """Put the knob as near to this x as the steps and the lowest value allow.

        Show the new opacity as a percent, and hand up the mirror with it.
        Do nothing when the opacity did not change.
        """
        opacity = self._slider.value_at(position_x)
        if opacity == self._slider.value:
            return

        self._slider.set_value(opacity)
        self._canvas.itemconfigure(self._percent, text=percent(opacity))
        self._on_changed(replace(self._mirror, opacity=opacity))
