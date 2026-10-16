"""The card of one mirror on the Mirrors page."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.mirror_card.button_bar import MirrorCardButtonBar
from tibia_mirror.ui.panel2.mirror_card.slider import MirrorCardSlider
from tibia_mirror.ui.panel2.mirror_card.title import MirrorCardTitle
from tibia_mirror.ui.panel2.mirror_info import MirrorInfo

# Sizes at 100% display scaling; px() scales them where they are used.
HEIGHT = 62
RADIUS = 8  # of the rounded corners


class MirrorCard(tk.Canvas):
    """The card of one mirror: its name and size, its buttons and its opacity slider."""

    def __init__(
        self,
        parent: tk.Misc,
        width: int,
        mirror: MirrorInfo,
        on_changed: Callable[[MirrorInfo], None],
    ) -> None:
        # No focus ring and no border: Tk adds both to a canvas.
        super().__init__(
            parent,
            width=width,
            height=px(HEIGHT),
            bg=theme.BG,
            highlightthickness=0,
            bd=0,
        )
        self._width = width
        self._mirror = mirror  # what the card shows
        self._on_changed = on_changed  # gets the new info after a change made on the card
        self._draw_background()

        self._title = MirrorCardTitle(self, self._width, self._mirror)
        self._button_bar = MirrorCardButtonBar(
            self, self._width, self._mirror, self._on_mirror_changed
        )
        self._slider = MirrorCardSlider(self, self._width, self._mirror)
        # the parts of the card: each one hears what the mouse does
        self._parts = (self._title, self._button_bar, self._slider)
        self._bind_events()

    def _draw_background(self) -> None:
        """The rounded shape of the card, a little lighter than the page."""
        self._background = rounded_image(
            self,
            width=self._width,
            height=px(HEIGHT),
            radius=px(RADIUS),
            colour=theme.SURFACE,
            background=theme.BG,
        )
        self.create_image(0, 0, anchor="nw", image=self._background)

    def destroy(self) -> None:
        """Close the hints of the card before it goes away."""
        for part in self._parts:
            part.pointer_left()

        super().destroy()

    def _bind_events(self) -> None:
        # <Enter> too: the pointer can come in and stop, with no <Motion> after it.
        self.bind("<Enter>", self._on_mouse_move)
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_mouse_move(self, event: tk.Event[tk.Canvas]) -> None:
        """Tell the parts where the pointer is. Show a hand over a place that can be clicked."""
        positions = event.x, event.y
        is_clickable: bool = False

        for part in self._parts:
            if part.pointer_moved(*positions):
                is_clickable = True

        cursor = "hand2" if is_clickable else ""

        self.configure(cursor=cursor)

    def _on_mouse_leave(self, event: tk.Event[tk.Canvas]) -> None:
        for part in self._parts:
            part.pointer_left()

        self.configure(cursor="")

    def _on_mouse_down(self, event: tk.Event[tk.Canvas]) -> None:
        for part in self._parts:
            part.pointer_pressed(event.x, event.y)

    def _on_mouse_up(self, event: tk.Event[tk.Canvas]) -> None:
        """Tell the parts, and look at the place under the pointer again."""
        for part in self._parts:
            part.pointer_released(event.x, event.y)

        self._on_mouse_move(event)

    def _on_mirror_changed(self, mirror: MirrorInfo) -> None:
        """Show a change made on the card in every part of it, and pass it on."""
        self._mirror = mirror

        for part in self._parts:
            part.set_mirror(mirror)

        self._on_changed(mirror)
