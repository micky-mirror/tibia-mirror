"""The box of a dropdown, which shows the chosen option and opens the menu of options."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Sequence

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import outlined_image
from tibia_mirror.ui.base.scale import px

# Sizes at 100% display scaling; px() scales them where they are used.
HEIGHT = 28  # as high as the options of a ChoiceRow
RADIUS = 8  # of the rounded corners
TEXT_X = 10  # from the left side of the box to the start of the text
ARROW_ROOM = 30  # kept free at the right side of the box, for the small arrow


class DropdownPicker(tk.Canvas):
    """A box with the chosen option. A click on it opens the menu with all options."""

    def __init__(
        self,
        parent: tk.Misc,
        options: Sequence[tuple[str, str]],
        selected: str,
        on_change: Callable[[str], None],
    ) -> None:
        # No focus ring and no border: Tk adds both to a canvas.
        super().__init__(
            parent,
            height=px(HEIGHT),
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
        )
        # (key, text) of each option, from top to bottom; tkinter itself uses self._options
        self._choices = options
        self._selected = selected  # the key of the chosen option
        self._on_change = on_change  # called with the key of the option the user chose
        self._width = self._get_width()

        self._normal_box = self._render_normal_box()

        self.configure(width=self._width)
        self._draw_box()

    def _get_width(self) -> int:
        """Room for the longest option and the small arrow."""
        font = tkfont.Font(font=theme.FONT)
        longest = max(font.measure(text) for _key, text in self._choices)

        return px(TEXT_X) + longest + px(ARROW_ROOM)

    def _render_normal_box(self) -> tk.PhotoImage:
        """The rounded shape of the box with a thin border, like the other fields of a card."""
        return outlined_image(
            self,
            width=self._width,
            height=px(HEIGHT),
            radius=px(RADIUS),
            colour=theme.SURFACE,
            border=theme.SURFACE_HI,
            background=theme.SURFACE,
        )

    def _draw_box(self) -> None:
        """The box in its normal look."""
        self._box = self.create_image(0, 0, anchor="nw", image=self._normal_box)
