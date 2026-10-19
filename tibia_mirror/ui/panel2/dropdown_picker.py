"""The box of a dropdown, which shows the chosen option and opens the menu of options."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Sequence

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import outlined_image, rounded_image
from tibia_mirror.ui.base.scale import px

ARROW_DOWN = "\ue70d"  # a small arrow that points down, from the Segoe MDL2 Assets icon font

# Sizes at 100% display scaling; px() scales them where they are used.
HEIGHT = 28  # as high as the options of a ChoiceRow
RADIUS = 8  # of the rounded corners
TEXT_X = 10  # from the left side of the box to the start of the text
ARROW_ROOM = 30  # kept free at the right side of the box, for the small arrow
ARROW_X = 16  # from the right side of the box to the middle of the arrow


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
            cursor="hand2",
        )
        # (key, text) of each option, from top to bottom; tkinter itself uses self._options
        self._choices = options
        self._selected = selected  # the key of the chosen option
        self._on_change = on_change  # called with the key of the option the user chose
        self._width = self._get_width()
        self._is_hovered = False  # True while the pointer is over the box

        self._normal_box = self._render_normal_box()
        self._bright_box = self._render_bright_box()

        self.configure(width=self._width)
        self._draw_box()
        self._draw_text()
        self._draw_arrow()
        self._bind_events()

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

    def _render_bright_box(self) -> tk.PhotoImage:
        """The rounded shape of the box, filled with the colour of its border."""
        return rounded_image(
            self,
            width=self._width,
            height=px(HEIGHT),
            radius=px(RADIUS),
            colour=theme.SURFACE_HI,
            background=theme.SURFACE,
        )

    def _draw_box(self) -> None:
        """The box in its normal look."""
        self._box = self.create_image(0, 0, anchor="nw", image=self._normal_box)

    def _draw_text(self) -> None:
        """The text of the chosen option, at the left, in the middle of the box's height."""
        self._text_item = self.create_text(
            px(TEXT_X),
            px(HEIGHT) // 2,
            text=self._get_selected_text(),
            anchor="w",
            font=theme.FONT,
            fill=theme.TEXT,
        )

    def _draw_arrow(self) -> None:
        """The small arrow at the right, in the middle of the box's height."""
        self._arrow = self.create_text(
            self._width - px(ARROW_X),
            px(HEIGHT) // 2,
            text=ARROW_DOWN,
            font=theme.FONT_ICON,
            fill=theme.SUBTEXT,
        )

    def _get_selected_text(self) -> str:
        return dict(self._choices)[self._selected]

    def _bind_events(self) -> None:
        self.bind("<Enter>", self._on_mouse_enter)
        self.bind("<Leave>", self._on_mouse_leave)

    def _on_mouse_enter(self, event: tk.Event[tk.Canvas]) -> None:
        self._set_hovered(True)

    def _on_mouse_leave(self, event: tk.Event[tk.Canvas]) -> None:
        self._set_hovered(False)

    def _set_hovered(self, is_hovered: bool) -> None:
        self._is_hovered = is_hovered
        self._update_look()

    def _update_look(self) -> None:
        """Show the box brighter while it is hovered or its menu is open."""
        box_image = self._bright_box if self._is_hovered else self._normal_box

        self.itemconfigure(self._box, image=box_image)
