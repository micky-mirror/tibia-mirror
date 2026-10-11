"""The dot in the colour of a mirror's frame, drawn on a canvas that something else owns."""

import tkinter as tk

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px


class ColourDot:
    """A round dot in the colour of a mirror's frame.

    While the pointer is over it, it shows a rounded shape behind the dot.
    """

    # Sizes at 100% display scaling; px() scales them where they are used.
    DOT_SIZE = 10
    SIZE = 22  # of the shape behind the dot, and of the place that reacts to the pointer
    SHAPE_RADIUS = 6  # of the corners of the shape behind the dot

    def __init__(self, canvas: tk.Canvas, middle_x: int, middle_y: int, colour: str) -> None:
        self._canvas = canvas
        self._middle_x = middle_x
        self._middle_y = middle_y
        self._colour = colour
        self._is_hovered = False  # True while the pointer is over the dot

        # the dot has smooth edges, so it needs one picture for each colour behind it
        self._normal_dot = self._render_dot(theme.SURFACE)
        self._hovered_dot = self._render_dot(theme.SURFACE_HI)

        # the shape first, so the dot lies on top of it
        self._draw_hover_shape()
        self._draw_dot()

    def contains(self, position_x: int, position_y: int) -> bool:
        """True when this place is on the dot, or very near to it."""
        half = px(self.SIZE) // 2
        is_in_width: bool = self._middle_x - half <= position_x < self._middle_x + half
        is_in_height: bool = self._middle_y - half <= position_y < self._middle_y + half
        return is_in_width and is_in_height

    def set_hovered(self, is_hovered: bool) -> None:
        """Show the hover look, or take it away. Do nothing when nothing changed."""
        if is_hovered == self._is_hovered:
            return
        self._is_hovered = is_hovered
        state = "normal" if is_hovered else "hidden"
        dot_image = self._hovered_dot if is_hovered else self._normal_dot

        self._canvas.itemconfigure(self._hover_shape, state=state)
        self._canvas.itemconfigure(self._dot, image=dot_image)

    def _render_dot(self, background: str) -> tk.PhotoImage:
        """The dot as an image, with its smooth edge made for the given colour behind it."""
        size = px(self.DOT_SIZE)
        return rounded_image(
            self._canvas,
            width=size,
            height=size,
            radius=size // 2,  # half of the size: a full circle
            colour=self._colour,
            background=background,
        )

    def _draw_hover_shape(self) -> None:
        """The rounded shape behind the dot. It is hidden until the pointer is over the dot."""
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

    def _draw_dot(self) -> None:
        self._dot = self._canvas.create_image(
            self._middle_x,
            self._middle_y,
            image=self._normal_dot,
        )
