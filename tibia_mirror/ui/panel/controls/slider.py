"""A horizontal slider drawn onto a canvas: rounded track, accent fill and a shadowed knob."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.core.geometry import slider_value, slider_x
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import raised_image, rounded_image
from tibia_mirror.ui.base.render import RaisedStyle, shadow_margins
from tibia_mirror.ui.base.scale import px

# Sizes at 100% display scaling; px() scales them where they are used.
TRACK_HEIGHT = 4
KNOB_SIZE = 14
KNOB_SHADOW_OFFSET = 1  # how far the shadow of the knob drops below it
KNOB_SHADOW_BLUR = 3  # how far the shadow of the knob fades out around it
HIT_HALF_HEIGHT = 11  # of the band around the track where a press moves the knob
HIT_SLACK = 4  # the band reaches this far past the ends of the track


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
        self._is_dragging = False  # True from a press on the slider until the button goes up
        # draw slider parts
        self._draw_track()
        self._add_fill()
        self._add_knob()
        self._update_knob()

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Move the knob with the pointer while the user drags it.

        With no drag, show the knob as active when the pointer is over the slider.
        Return True when a press at this place would move the knob.
        """
        if self._is_dragging:
            self._move_knob(position_x)
            return True

        is_over_slider = self._contains(position_x, position_y)
        self._set_active(is_over_slider)

        return is_over_slider

    def pointer_left(self) -> None:
        """The pointer went out of the canvas: the knob is not shown as active."""
        # a drag goes on outside the canvas, and the knob stays active until it ends
        if not self._is_dragging:
            self._set_active(False)

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Start a drag if the button went down on the slider: the knob jumps to the pointer."""
        if self._contains(position_x, position_y):
            self._is_dragging = True
            self._move_knob(position_x)

    def pointer_released(self) -> None:
        """End the drag."""
        self._is_dragging = False

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

    def _move_knob(self, position_x: int) -> None:
        """Put the knob as near to this x as the steps and the lowest value allow.

        Hand over the new value. Do nothing when the value did not change.
        """
        value = self._get_value_at(position_x)

        if value == self._value:
            return

        self._value = value
        self._update_knob()
        self._on_change(value)

    def _set_active(self, is_active: bool) -> None:
        """Show the knob in its active look, or in its normal look."""
        self._canvas.itemconfigure(self._knob, image=self._knob_images[is_active])

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
        shadow_room = shadow_margins(self._get_knob_style(is_active=False))
        half_knob = px(KNOB_SIZE) / 2
        image_left = round(knob_x - half_knob - shadow_room.left)
        image_top = round(self._middle_y - half_knob - shadow_room.top)

        self._canvas.coords(self._knob, image_left, image_top)

    def _get_knob_image(self, is_active: bool) -> tk.PhotoImage:
        size = px(KNOB_SIZE)
        style = self._get_knob_style(is_active)

        return raised_image(
            self._canvas,
            width=size,
            height=size,
            style=style,
            background=theme.SURFACE,
        )

    def _get_knob_style(self, is_active: bool) -> RaisedStyle:
        """A round shape with a soft shadow, in its own colour while the knob is active."""
        colour = theme.KNOB_ACTIVE if is_active else theme.KNOB

        return RaisedStyle(
            fill=colour,
            radius=px(KNOB_SIZE) // 2,
            shadow_alpha=0.45 * theme.SHADOW,
            shadow_offset=px(KNOB_SHADOW_OFFSET),
            shadow_blur=px(KNOB_SHADOW_BLUR),
        )

    def _contains(self, position_x: int, position_y: int) -> bool:
        """Whether a press here moves the knob: on the track, or a little around it."""
        slack = px(HIT_SLACK)
        is_inside_x = self._left - slack <= position_x <= self._right + slack
        is_inside_y = abs(position_y - self._middle_y) <= px(HIT_HALF_HEIGHT)

        return is_inside_x and is_inside_y

    def _get_value_at(self, position_x: int) -> float:
        """The value for a knob at this x, in steps, and never below the lowest value."""
        knob_left, knob_right = self._get_knob_range()
        value = slider_value(position_x, knob_left, knob_right, self._start, self._end, self._step)

        return max(self._lowest, value)

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
