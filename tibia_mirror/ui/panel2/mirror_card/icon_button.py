"""A small button with only an icon, drawn on a canvas that something else owns."""

import tkinter as tk

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px


class IconButton:
    """A small square button with only an icon.

    While the pointer is over it, it shows a rounded shape behind the icon.
    """

    # Sizes at 100% display scaling; px() scales them where they are used.
    SIZE = 26  # the button is square, so this is its width and its height
    SHAPE_RADIUS = 6  # of the corners of the shape behind the icon

    def __init__(
        self,
        canvas: tk.Canvas,
        middle_x: int,
        middle_y: int,
        icon: str,
        font: theme.FontSpec,
        colour: str,
        hovered_colour: str,
    ) -> None:
        self._canvas = canvas
        self._middle_x = middle_x
        self._middle_y = middle_y
        self._icon = icon
        self._font = font
        self._colour = colour
        self._hovered_colour = hovered_colour  # of the icon while the pointer is over the button
        self._is_hovered = False  # True while the pointer is over the button

        # the shape first, so the icon lies on top of it
        self._draw_hover_shape()
        self._draw_icon()

    def contains(self, position_x: int, position_y: int) -> bool:
        """True when this place is inside the button."""
        half = px(self.SIZE) // 2
        is_in_width: bool = self._middle_x - half <= position_x < self._middle_x + half
        is_in_height: bool = self._middle_y - half <= position_y < self._middle_y + half
        return is_in_width and is_in_height

    def set_hovered(self, is_hovered: bool) -> None:
        """Show the hover look, or take it away. Do nothing when nothing changed."""
        if is_hovered == self._is_hovered:
            return
        self._is_hovered = is_hovered
        self._update_look()

    def _update_look(self) -> None:
        """While hovered: the shape behind the icon, and the icon in its hovered colour."""
        state = "normal" if self._is_hovered else "hidden"
        icon_colour = self._hovered_colour if self._is_hovered else self._colour

        self._canvas.itemconfigure(self._hover_shape, state=state)
        self._canvas.itemconfigure(self._icon_item, fill=icon_colour)

    def _draw_hover_shape(self) -> None:
        """The rounded shape behind the icon. It is hidden until the pointer is over the button."""
        size = px(self.SIZE)
        self._hover_shape_image = rounded_image(
            self._canvas,
            width=size,
            height=size,
            radius=px(self.SHAPE_RADIUS),
            colour=theme.SURFACE_HI,
            background=theme.SURFACE,  # the colour of the card around the shape
        )
        self._hover_shape = self._canvas.create_image(
            self._middle_x,
            self._middle_y,
            image=self._hover_shape_image,
            state="hidden",
        )

    def _draw_icon(self) -> None:
        self._icon_item = self._canvas.create_text(
            self._middle_x,
            self._middle_y,
            text=self._icon,
            font=self._font,
            fill=self._colour,
        )
