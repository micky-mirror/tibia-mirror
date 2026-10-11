"""The box on the Mirrors page that shows the active profile and opens the profile menu."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Sequence
from functools import partial

from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import elide
from tibia_mirror.ui.controls.menu import SEPARATOR, MenuItem, PopupMenu

ICON = "\ue77b"  # a person, from the Segoe MDL2 Assets icon font
ARROW_DOWN = "\ue70d"  # a small arrow that points down, from the same icon font
ARROW_UP = "\ue70e"  # the same arrow, pointing up

# Sizes at 100% display scaling; px() scales them where they are used.
HEIGHT = 36
RADIUS = 8  # of the rounded corners
ICON_X = 20  # from the left side of the box to the middle of the icon
NAME_X = 38  # from the left side of the box to the start of the name
ARROW_ROOM = 34  # kept free at the right side of the box, for the small arrow
ARROW_X = 18  # from the right side of the box to the middle of the arrow


class ProfilePicker(tk.Canvas):
    """A box with the name of the active profile. A click on it opens the profile menu."""

    def __init__(
        self, parent: tk.Misc, width: int, name: str, profile_names: Sequence[str]
    ) -> None:
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
        self._profile_names = profile_names  # the names of all profiles, for the menu
        self._is_hovered = False  # True while the pointer is over the box
        self._is_open = False  # True while the profile menu is open

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
        self._arrow = self.create_text(
            self._width - px(ARROW_X),
            px(HEIGHT) // 2,
            text=ARROW_DOWN,
            font=theme.FONT_ICON,
            fill=theme.SUBTEXT,
        )

    def _bind_events(self) -> None:
        self.bind("<Enter>", self._on_mouse_enter)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_mouse_enter(self, event: tk.Event[tk.Canvas]) -> None:
        self._set_hovered(True)

    def _on_mouse_leave(self, event: tk.Event[tk.Canvas]) -> None:
        self._set_hovered(False)

    def _set_hovered(self, is_hovered: bool) -> None:
        self._is_hovered = is_hovered
        self._update_look()

    def _set_open(self, is_open: bool) -> None:
        self._is_open = is_open
        self._update_look()

    def _update_look(self) -> None:
        """Show the box brighter while it is hovered or its menu is open.

        The arrow points up while the menu is open.
        """
        is_bright: bool = self._is_hovered or self._is_open
        self.itemconfigure(self._box, image=self._bright_box if is_bright else self._normal_box)
        self.itemconfigure(self._arrow, text=ARROW_UP if self._is_open else ARROW_DOWN)

    def _on_mouse_up(self, event: tk.Event[tk.Canvas]) -> None:
        """Open the profile menu if the button went up inside the box."""
        # after a drag the button can go up outside the box
        is_inside: bool = 0 <= event.x < self._width and 0 <= event.y < px(HEIGHT)
        if is_inside and not self._is_open:
            self._open_menu()

    def _open_menu(self) -> None:
        """Open the profile menu under the box, as wide as the box."""
        self._set_open(True)
        # the menu is its own small window, so it needs the place of the box on the screen
        left = self.winfo_rootx()
        top = self.winfo_rooty()
        box = (left, top, left + self._width, top + px(HEIGHT))
        PopupMenu(self.winfo_toplevel(), box, self._menu_items(), on_close=self._on_menu_closed)

    def _on_menu_closed(self) -> None:
        self._set_open(False)

    def _menu_items(self) -> list[MenuItem | None]:
        """The entries of the menu: every profile, then what can be done with profiles."""
        return [
            *self._profile_items(),
            SEPARATOR,
            MenuItem(tr("New profile…"), self._new),
            MenuItem(tr("Duplicate…"), self._duplicate),
            MenuItem(tr("Rename…"), self._rename),
        ]

    def _profile_items(self) -> list[MenuItem]:
        """One entry for each profile, with a check mark at the active one."""
        return [
            MenuItem(name, partial(self._select, name), checked=name == self._profile_name)
            for name in self._profile_names
        ]

    def _select(self, name: str) -> None:
        """Make the profile `name` the active one."""

    def _new(self) -> None:
        """Ask for a name and make a new, empty profile."""

    def _duplicate(self) -> None:
        """Ask for a name and make a copy of the active profile."""

    def _rename(self) -> None:
        """Ask for a new name for the active profile."""
