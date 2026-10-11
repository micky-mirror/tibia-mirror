"""The box on the Mirrors page that shows the active profile and opens the profile menu."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import elide

ICON = "\ue77b"  # a person, from the Segoe MDL2 Assets icon font
ARROW_DOWN = "\ue70d"  # a small arrow that points down, from the same icon font

# Sizes at 100% display scaling; px() scales them where they are used.
HEIGHT = 36
RADIUS = 8  # of the rounded corners
ICON_X = 20  # from the left side of the box to the middle of the icon
NAME_X = 38  # from the left side of the box to the start of the name
ARROW_ROOM = 34  # kept free at the right side of the box, for the small arrow
ARROW_X = 18  # from the right side of the box to the middle of the arrow


class ProfilePicker(tk.Canvas):
    """A box with the name of the active profile. A click on it opens the profile menu."""

    def __init__(self, parent: tk.Misc, width: int, name: str) -> None:
        # No focus ring and no border: Tk adds both to a canvas.
        super().__init__(
            parent,
            width=width,
            height=px(HEIGHT),
            bg=theme.BG,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._width = width
        self._profile_name = name  # the name of the active profile

        self._normal_box = self._render_box(theme.SURFACE)
        self._bright_box = self._render_box(theme.SURFACE_HI)

        self._draw_box()
        self._draw_icon()
        self._draw_name()
        self._draw_arrow()
        self._bind_events()

    def _render_box(self, colour: str) -> tk.PhotoImage:
        """The rounded shape of the box, as an image in the given colour."""
        return rounded_image(
            self,
            width=self._width,
            height=px(HEIGHT),
            radius=px(RADIUS),
            colour=colour,
            background=theme.BG,
        )

    def _draw_box(self) -> None:
        """The box in its normal look, a little lighter than the page."""
        self._box = self.create_image(0, 0, anchor="nw", image=self._normal_box)

    def _draw_icon(self) -> None:
        """The small person icon at the left, in the middle of the box's height."""
        self.create_text(
            px(ICON_X),
            px(HEIGHT) // 2,
            text=ICON,
            font=theme.FONT_ICON,
            fill=theme.SUBTEXT,
        )

    def _draw_name(self) -> None:
        """The name of the active profile, cut short with "…" when it is too long for the box."""
        font = tkfont.Font(font=theme.FONT_BOLD)
        room = self._width - px(NAME_X) - px(ARROW_ROOM)  # the width the name can take
        self.create_text(
            px(NAME_X),
            px(HEIGHT) // 2,
            text=elide(self._profile_name, font, room),
            anchor="w",
            font=font,
            fill=theme.TEXT,
        )

    def _draw_arrow(self) -> None:
        """The small arrow at the right, in the middle of the box's height."""
        self.create_text(
            self._width - px(ARROW_X),
            px(HEIGHT) // 2,
            text=ARROW_DOWN,
            font=theme.FONT_ICON,
            fill=theme.SUBTEXT,
        )

    def _bind_events(self) -> None:
        self.bind("<Enter>", self._on_mouse_enter)
        self.bind("<Leave>", self._on_mouse_leave)

    def _on_mouse_enter(self, event: tk.Event[tk.Canvas]) -> None:
        self._set_hovered(True)

    def _on_mouse_leave(self, event: tk.Event[tk.Canvas]) -> None:
        self._set_hovered(False)

    def _set_hovered(self, is_hovered: bool) -> None:
        """Show the box brighter while the pointer is over it."""
        box_image = self._bright_box if is_hovered else self._normal_box
        self.itemconfigure(self._box, image=box_image)
