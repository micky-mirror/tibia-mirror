"""A horizontal slider drawn onto a canvas: rounded track, accent fill and a shadowed knob."""

import tkinter as tk
from dataclasses import replace

from tibia_mirror.core.geometry import slider_value, slider_x
from tibia_mirror.ui import theme
from tibia_mirror.ui.images import photo
from tibia_mirror.ui.render import ButtonStyle, button_pixels, margins
from tibia_mirror.ui.scale import px


class SliderDrawing:
    """A slider drawn on `canvas` from x0 to x1 at height y, mapping pointer x to values.

    `floor` is the lowest value the knob stops at. The owner handles the mouse
    through contains(), value_at(), set_value() and set_active().
    """

    # Sizes at 100% display scaling, scaled with px() where used.
    TRACK_HEIGHT = 4
    KNOB = 14
    HIT_HALF_HEIGHT = 11  # of the clickable band around the track
    HIT_SLACK_X = 4  # the clickable band reaches this far past the track's ends
    KNOB_SHADOW_OFFSET = 1
    KNOB_SHADOW_BLUR = 3

    def __init__(
        self,
        canvas: tk.Canvas,
        x0: int,
        x1: int,
        y: int,
        value: float,
        *,
        lo: float,
        hi: float,
        step: float,
        floor: float | None = None,
        background: str | None = None,
    ) -> None:
        background = theme.SURFACE if background is None else background
        self._canvas = canvas
        self._x0, self._x1, self._y = x0, x1, y
        self._lo, self._hi, self._step = lo, hi, step
        self._floor = lo if floor is None else floor
        self._background = background
        self._track_height, self._knob_size = px(self.TRACK_HEIGHT), px(self.KNOB)
        self._knob_x0 = x0 + self._knob_size / 2
        self._knob_x1 = x1 - self._knob_size / 2
        top = y - self._track_height / 2

        inactive = ButtonStyle(fill=theme.SURFACE_HI, radius=self._track_height // 2)
        self._track_img = photo(
            canvas, button_pixels(x1 - x0, self._track_height, inactive, background)
        )
        canvas.create_image(x0, top, anchor="nw", image=self._track_img)
        self._fill_img: tk.PhotoImage | None = None
        self._fill = canvas.create_image(x0, top, anchor="nw")

        knob = ButtonStyle(
            fill=theme.KNOB,
            radius=self._knob_size // 2,
            shadow_alpha=0.45 * theme.SHADOW,
            shadow_offset=px(self.KNOB_SHADOW_OFFSET),
            shadow_blur=px(self.KNOB_SHADOW_BLUR),
        )
        self._knob_margins = margins(knob)
        self._knob_imgs = {
            active: photo(
                canvas,
                button_pixels(
                    self._knob_size,
                    self._knob_size,
                    replace(knob, fill=theme.KNOB_ACTIVE if active else theme.KNOB),
                    background,
                ),
            )
            for active in (False, True)
        }
        self._knob = canvas.create_image(0, 0, anchor="nw", image=self._knob_imgs[False])
        self._active = False
        self.value = value
        self._draw()

    def contains(self, x: int, y: int) -> bool:
        slack = px(self.HIT_SLACK_X)
        in_band = abs(y - self._y) <= px(self.HIT_HALF_HEIGHT)
        return self._x0 - slack <= x <= self._x1 + slack and in_band

    def value_at(self, x: int) -> float:
        value = slider_value(x, self._knob_x0, self._knob_x1, self._lo, self._hi, self._step)
        return max(self._floor, value)

    def set_value(self, value: float) -> None:
        if value != self.value:
            self.value = value
            self._draw()

    def set_active(self, active: bool) -> None:
        if active != self._active:
            self._active = active
            self._canvas.itemconfigure(self._knob, image=self._knob_imgs[active])

    def _draw(self) -> None:
        knob_x = slider_x(self.value, self._knob_x0, self._knob_x1, self._lo, self._hi)
        fill_width = max(self._track_height, round(knob_x - self._x0))
        accent = ButtonStyle(fill=theme.ACCENT, radius=self._track_height // 2)
        self._fill_img = photo(
            self._canvas, button_pixels(fill_width, self._track_height, accent, self._background)
        )
        self._canvas.itemconfigure(self._fill, image=self._fill_img)
        margins = self._knob_margins
        self._canvas.coords(
            self._knob,
            round(knob_x - self._knob_size / 2 - margins.left),
            round(self._y - self._knob_size / 2 - margins.top),
        )
