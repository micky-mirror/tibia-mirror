"""The dot in the colour of a mirror's frame, drawn on a canvas that something else owns."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.core.geometry import Box
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.tooltip import Tooltip
from tibia_mirror.ui.panel.mirrors.mirror_card.tip import Tip


class ColourDot:
    """A round dot in the colour of a mirror's frame.

    While the pointer is over it, it shows a rounded shape behind the dot.
    """

    # Sizes at 100% display scaling; px() scales them where they are used.
    DOT_SIZE = 10
    SIZE = 22  # of the shape behind the dot, and of the place that reacts to the pointer
    SHAPE_RADIUS = 6  # of the corners of the shape behind the dot

    def __init__(
        self,
        canvas: tk.Canvas,
        middle_x: int,
        middle_y: int,
        colour: str,
        tip: Tip,
        on_click: Callable[[], None],
    ) -> None:
        self._canvas = canvas
        self._middle_x = middle_x
        self._middle_y = middle_y
        self._colour = colour
        self._tip = tip  # the hint that opens while the pointer rests on the dot
        self._tooltip = Tooltip(canvas.winfo_toplevel())
        self._on_click = on_click  # what the dot does when it is clicked
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
        self._update_look()
        self._update_tip()

    def click(self) -> None:
        """Do what the dot is for."""
        self._on_click()

    def set_colour(self, colour: str) -> None:
        """Draw the dot in a new colour. Do nothing when the colour is the same."""
        if colour == self._colour:
            return

        self._colour = colour
        self._normal_dot = self._render_dot(theme.SURFACE)
        self._hovered_dot = self._render_dot(theme.SURFACE_HI)
        self._update_look()

    def _update_look(self) -> None:
        """While hovered: the shape behind the dot, and the dot made for that shape."""
        state = "normal" if self._is_hovered else "hidden"
        dot_image = self._hovered_dot if self._is_hovered else self._normal_dot

        self._canvas.itemconfigure(self._hover_shape, state=state)
        self._canvas.itemconfigure(self._dot, image=dot_image)

    def _update_tip(self) -> None:
        """Open the hint while the dot is hovered, and close it when it is not."""
        if self._is_hovered:
            self._tooltip.show(self._tip.title, self.get_screen_box(), self._tip.detail)
        else:
            self._tooltip.hide()

    def get_screen_box(self) -> Box:
        """The screen place of the dot's hover shape. Hints and the colour choice open under it."""
        half = px(self.SIZE) // 2
        middle_x = self._canvas.winfo_rootx() + self._middle_x
        middle_y = self._canvas.winfo_rooty() + self._middle_y
        return (middle_x - half, middle_y - half, middle_x + half, middle_y + half)

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
