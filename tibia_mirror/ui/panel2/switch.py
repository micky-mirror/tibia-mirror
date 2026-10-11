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

    def __init__(self, canvas: tk.Canvas, right: int, middle_y: int, is_on: bool) -> None:
        self._canvas = canvas
        left = right - px(self.WIDTH)
        top = middle_y - px(self.HEIGHT) // 2
        self._track = canvas.create_image(left, top, anchor="nw")
        self.draw(is_on)

    def draw(self, is_on: bool) -> None:
        """Show the switch as on or off."""
        colour = theme.ACCENT if is_on else theme.SURFACE_HI
        # fully round ends: the radius is half of the height
        style = ButtonStyle(fill=colour, radius=px(self.HEIGHT) // 2)
        # theme.SURFACE is the colour of the card, seen around the round ends
        pixels = button_pixels(px(self.WIDTH), px(self.HEIGHT), style, theme.SURFACE)
        # Tk shows an image only while Python keeps it, so the switch stores it.
        self._track_image = photo(self._canvas, pixels)
        self._canvas.itemconfigure(self._track, image=self._track_image)
