"""A raised button: a rounded button with a soft shadow, drawn on its own canvas."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from dataclasses import replace

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import photo
from tibia_mirror.ui.base.render import ButtonStyle, button_pixels, margins

# A pressed button's picture is 1px lower at any display scaling, so its text drops by the same.
PRESSED_SINK = 1


class RaisedButton(tk.Canvas):
    """A rounded button with a soft shadow, lighter while hovered and sunk while pressed.

    The canvas is bigger than the button by `margins`, the room for the shadow around it.
    """

    def __init__(
        self,
        parent: tk.Misc,
        text: str,
        command: Callable[[], None],
        *,
        width: int,
        height: int,
        style: ButtonStyle,
        hover_fill: str,
        font: theme.FontSpec,
        text_colour: str,
        background: str,
    ) -> None:
        self.margins = margins(style)  # room for the shadow on each side of the button
        super().__init__(
            parent,
            width=self.margins.left + width + self.margins.right,
            height=self.margins.top + height + self.margins.bottom,
            bg=background,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._text = text
        self._command = command  # called when the button is clicked
        self._width = width  # of the button itself, without its shadow
        self._height = height  # of the button itself, without its shadow
        self._style = style
        self._hover_fill = hover_fill  # the colour of the button while the pointer is on it
        self._font = font
        self._text_colour = text_colour
        self._background = background  # the colour behind the button; its shadow fades into it
        self._is_hovered = False
        self._is_pressed = False  # True from a press on the button until the mouse button goes up
        # draw button parts
        self._add_images()
        self._add_text()
        self._bind_events()

    def _add_images(self) -> None:
        """The button in each of its looks: normal, hovered and pressed."""
        hovered_style = replace(self._style, fill=self._hover_fill)

        self._images = {
            "normal": self._get_image(self._style, is_pressed=False),
            "hovered": self._get_image(hovered_style, is_pressed=False),
            "pressed": self._get_image(hovered_style, is_pressed=True),
        }
        self._image_item = self.create_image(0, 0, anchor="nw", image=self._images["normal"])

    def _add_text(self) -> None:
        """The text in the middle of the button."""
        middle_x, middle_y = self._get_text_position()

        self._text_item = self.create_text(
            middle_x, middle_y, text=self._text, font=self._font, fill=self._text_colour
        )

    def _bind_events(self) -> None:
        self.bind("<Enter>", self._on_mouse_enter)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_mouse_enter(self, event: tk.Event[tk.Canvas]) -> None:
        self._is_hovered = True
        self._update_look()

    def _on_mouse_leave(self, event: tk.Event[tk.Canvas]) -> None:
        self._is_hovered = False
        self._update_look()

    def _on_mouse_down(self, event: tk.Event[tk.Canvas]) -> None:
        self._is_pressed = True
        self._update_look()

    def _on_mouse_up(self, event: tk.Event[tk.Canvas]) -> None:
        # a click only when the mouse button went down and up on the button
        is_click = self._is_pressed and self._is_hovered
        self._is_pressed = False
        self._update_look()

        if is_click:
            self._command()

    def _update_look(self) -> None:
        """Show the picture of the current look, and drop the text with a pressed button."""
        look = self._get_look()
        middle_x, middle_y = self._get_text_position()
        sink = PRESSED_SINK if look == "pressed" else 0

        self.itemconfigure(self._image_item, image=self._images[look])
        self.coords(self._text_item, middle_x, middle_y + sink)

    def _get_look(self) -> str:
        """Pressed while it is down with the pointer on it, hovered while only pointed at."""
        if self._is_pressed and self._is_hovered:
            return "pressed"

        if self._is_hovered:
            return "hovered"

        return "normal"

    def _get_image(self, style: ButtonStyle, *, is_pressed: bool) -> tk.PhotoImage:
        """The button and its shadow. Pressed, it is a pixel lower and its shadow is flatter."""
        pixels = button_pixels(self._width, self._height, style, self._background, is_pressed)

        return photo(self, pixels)

    def _get_text_position(self) -> tuple[float, float]:
        """The middle of the button, inside the room for the shadow."""
        middle_x = self.margins.left + self._width / 2
        middle_y = self.margins.top + self._height / 2

        return middle_x, middle_y
