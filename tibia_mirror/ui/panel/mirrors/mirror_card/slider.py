"""The opacity slider of a mirror card, with the opacity as a percent."""

import tkinter as tk
from collections.abc import Callable
from dataclasses import replace

from tibia_mirror.config import MIN_OPACITY, OPACITY_STEP
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import percent
from tibia_mirror.ui.panel.controls.slider import Slider
from tibia_mirror.ui.panel.mirrors.mirror_info import MirrorInfo

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

        self._draw_slider()
        self._draw_percent()

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Pass the pointer on to the slider. Return True when a press here would move the knob."""
        return self._slider.pointer_moved(position_x, position_y)

    def pointer_left(self) -> None:
        self._slider.pointer_left()

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        self._slider.pointer_pressed(position_x, position_y)

    def pointer_released(self, position_x: int, position_y: int) -> None:
        self._slider.pointer_released()

    def set_mirror(self, mirror: MirrorInfo) -> None:
        """Keep the new state of the mirror."""
        self._mirror = mirror

    def _draw_slider(self) -> None:
        """The slider, from the left side space of the card to the room of the percent."""
        position_x_start = px(SIDE_PAD)
        position_x_end = self._width - px(SIDE_PAD) - px(PERCENT_ROOM)

        self._slider = Slider(
            self._canvas,
            position_x_start,
            position_x_end,
            px(SLIDER_Y),
            self._mirror.opacity,
            start=0.0,
            end=1.0,
            step=OPACITY_STEP,
            lowest=MIN_OPACITY,
            on_change=self._on_opacity_changed,
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

    def _on_opacity_changed(self, opacity: float) -> None:
        """Show the new opacity as a percent, and hand up the mirror with it."""
        self._canvas.itemconfigure(self._percent, text=percent(opacity))
        self._on_changed(replace(self._mirror, opacity=opacity))
