"""The box on the Mirrors page that shows the active profile and opens the profile menu."""

import tkinter as tk
import tkinter.font as tkfont

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import elide

ICON = "\ue77b"  # a person, from the Segoe MDL2 Assets icon font

# Sizes at 100% display scaling; px() scales them where they are used.
HEIGHT = 36
RADIUS = 8  # of the rounded corners
ICON_X = 20  # from the left side of the box to the middle of the icon
NAME_X = 38  # from the left side of the box to the start of the name
ARROW_ROOM = 34  # kept free at the right side of the box, for the small arrow


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
        )
        self._width = width
        self._profile_name = name  # the name of the active profile
        self._draw_box()
        self._draw_icon()
        self._draw_name()

    def _draw_box(self) -> None:
        """The rounded shape of the box, a little lighter than the page."""
        self._box_image = rounded_image(
            self,
            width=self._width,
            height=px(HEIGHT),
            radius=px(RADIUS),
            colour=theme.SURFACE,
            background=theme.BG,
        )
        self.create_image(0, 0, anchor="nw", image=self._box_image)

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
