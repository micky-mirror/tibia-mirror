"""A horizontal slider drawn onto a canvas: rounded track, accent fill and a shadowed knob."""

import tkinter as tk
from collections.abc import Callable
from dataclasses import replace

from tibia_mirror.core.geometry import slider_value, slider_x
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import photo, rounded_image
from tibia_mirror.ui.base.render import ButtonStyle, button_pixels, margins
from tibia_mirror.ui.base.scale import px


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


# Sizes at 100% display scaling; px() scales them where they are used.
TRACK_HEIGHT = 4
KNOB_SIZE = 14
KNOB_SHADOW_OFFSET = 1  # how far the shadow of the knob drops below it
KNOB_SHADOW_BLUR = 3  # how far the shadow of the knob fades out around it


class Slider:
    """A slider drawn on a canvas, that sets a number with its knob."""

    def __init__(
        self,
        canvas: tk.Canvas,
        left: int,
        right: int,
        middle_y: int,
        value: float,
        *,
        start: float,
        end: float,
        step: float,
        lowest: float,
        on_change: Callable[[float], None],
    ) -> None:
        self._canvas = canvas
        self._left = left  # where the track starts on the canvas
        self._right = right  # where the track ends
        self._middle_y = middle_y  # the middle line of the track and of the knob
        self._value = value
        self._start = start  # the value at the left end of the track
        self._end = end  # the value at the right end of the track
        self._step = step  # the knob moves in steps of this size
        self._lowest = lowest  # the knob does not go below this value
        self._on_change = on_change  # called with the new value each time the knob moves a step
        # draw slider parts
        self._draw_track()
        self._add_fill()
        self._add_knob()
        self._update_knob()

    def _draw_track(self) -> None:
        """The grey rounded line the knob moves along."""
        height = px(TRACK_HEIGHT)
        self._track_image = rounded_image(
            self._canvas,
            width=self._right - self._left,
            height=height,
            radius=height // 2,
            colour=theme.SURFACE_HI,
            background=theme.SURFACE,
        )

        self._canvas.create_image(
            self._left, self._get_track_top_y(), anchor="nw", image=self._track_image
        )

    def _add_fill(self) -> None:
        """The accent part of the track, from its left end to the knob."""
        self._fill_image: tk.PhotoImage | None = None  # drawn again each time the knob moves
        self._fill = self._canvas.create_image(self._left, self._get_track_top_y(), anchor="nw")

    def _add_knob(self) -> None:
        """The round knob, in its normal look and in its active look."""
        self._knob_images = {
            is_active: self._get_knob_image(is_active) for is_active in (False, True)
        }
        self._knob = self._canvas.create_image(0, 0, anchor="nw", image=self._knob_images[False])

    def _update_knob(self) -> None:
        """Put the knob at the value, and draw the accent part of the track up to it."""
        knob_x = self._get_knob_x()

        self._draw_fill(knob_x)
        self._place_knob(knob_x)

    def _draw_fill(self, knob_x: float) -> None:
        """The accent part of the track up to `knob_x`, never shorter than its round ends."""
        height = px(TRACK_HEIGHT)
        width = max(height, round(knob_x - self._left))

        self._fill_image = rounded_image(
            self._canvas,
            width=width,
            height=height,
            radius=height // 2,
            colour=theme.ACCENT,
            background=theme.SURFACE,
        )
        self._canvas.itemconfigure(self._fill, image=self._fill_image)

    def _place_knob(self, knob_x: float) -> None:
        """Put the middle of the knob at `knob_x`. Its image is bigger, for the shadow."""
        shadow_room = margins(self._get_knob_style(is_active=False))
        half_knob = px(KNOB_SIZE) / 2
        image_left = round(knob_x - half_knob - shadow_room.left)
        image_top = round(self._middle_y - half_knob - shadow_room.top)

        self._canvas.coords(self._knob, image_left, image_top)

    def _get_knob_image(self, is_active: bool) -> tk.PhotoImage:
        size = px(KNOB_SIZE)
        pixels = button_pixels(size, size, self._get_knob_style(is_active), theme.SURFACE)

        return photo(self._canvas, pixels)

    def _get_knob_style(self, is_active: bool) -> ButtonStyle:
        """A round shape with a soft shadow, in its own colour while the knob is active."""
        colour = theme.KNOB_ACTIVE if is_active else theme.KNOB

        return ButtonStyle(
            fill=colour,
            radius=px(KNOB_SIZE) // 2,
            shadow_alpha=0.45 * theme.SHADOW,
            shadow_offset=px(KNOB_SHADOW_OFFSET),
            shadow_blur=px(KNOB_SHADOW_BLUR),
        )

    def _get_knob_x(self) -> float:
        """The middle of the knob for the value."""
        knob_left, knob_right = self._get_knob_range()

        return slider_x(self._value, knob_left, knob_right, self._start, self._end)

    def _get_knob_range(self) -> tuple[float, float]:
        """The leftmost and the rightmost middle of the knob, so it stays on the track."""
        half_knob = px(KNOB_SIZE) / 2

        return self._left + half_knob, self._right - half_knob

    def _get_track_top_y(self) -> float:
        return self._middle_y - px(TRACK_HEIGHT) / 2
