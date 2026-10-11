"""An on/off switch, drawn on a canvas that something else owns."""

import tkinter as tk

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import photo
from tibia_mirror.ui.base.render import ButtonStyle, button_pixels
from tibia_mirror.ui.base.scale import px


class Switch:
    """An on/off switch: a rounded track with a round knob inside.

    The knob is at the left when the switch is off and at the right when it is on.
    """

    # Sizes at 100% display scaling; px() scales them where they are used.
    WIDTH = 36
    HEIGHT = 20
    KNOB_SIZE = 12  # the knob is round, so this is its width and its height

    def __init__(self, canvas: tk.Canvas, right: int, middle_y: int, is_on: bool) -> None:
        self._canvas = canvas
        self._left = right - px(self.WIDTH)  # the left end of the track
        self._middle_y = middle_y
        top = middle_y - px(self.HEIGHT) // 2
        self._track = canvas.create_image(self._left, top, anchor="nw")
        # draw() puts the knob at its place
        self._knob = canvas.create_image(0, middle_y, anchor="w")
        self.draw(is_on)

    def draw(self, is_on: bool) -> None:
        """Show the switch as on or off."""
        self._draw_track(is_on)
        self._draw_knob(is_on)

    def _draw_track(self, is_on: bool) -> None:
        """The rounded track, in the accent colour when the switch is on."""
        # fully round ends: the radius is half of the height
        style = ButtonStyle(fill=self._track_colour(is_on), radius=px(self.HEIGHT) // 2)
        # theme.SURFACE is the colour of the card, seen around the round ends
        pixels = button_pixels(px(self.WIDTH), px(self.HEIGHT), style, theme.SURFACE)
        # Tk shows an image only while Python keeps it, so the switch stores it.
        self._track_image = photo(self._canvas, pixels)
        self._canvas.itemconfigure(self._track, image=self._track_image)

    def _draw_knob(self, is_on: bool) -> None:
        """The round knob, at the left when the switch is off and at the right when it is on."""
        size = px(self.KNOB_SIZE)
        colour = theme.ON_ACCENT if is_on else theme.TEXT
        style = ButtonStyle(fill=colour, radius=size // 2)
        # the track is seen around the knob, so the track's colour is the background
        pixels = button_pixels(size, size, style, self._track_colour(is_on))
        self._knob_image = photo(self._canvas, pixels)
        self._canvas.itemconfigure(self._knob, image=self._knob_image)
        self._canvas.coords(self._knob, self._knob_x(is_on), self._middle_y)

    def _knob_x(self, is_on: bool) -> int:
        """The x of the left side of the knob."""
        # the knob has the same space around it on every side inside the track
        space = (px(self.HEIGHT) - px(self.KNOB_SIZE)) // 2
        if is_on:
            return self._left + px(self.WIDTH) - space - px(self.KNOB_SIZE)
        return self._left + space

    def _track_colour(self, is_on: bool) -> str:
        return theme.ACCENT if is_on else theme.SURFACE_HI
