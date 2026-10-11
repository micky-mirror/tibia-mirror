"""The menu on the left side of the panel."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px

# The menu entries: key -> (icon, label in English).
ENTRIES = {
    "mirrors": ("\ue8b9", "Mirrors"),
    "shortcuts": ("\ue765", "Shortcuts"),
    "about": ("\ue946", "About"),
    "settings": ("\ue713", "Settings"),
}


class NavRail(tk.Canvas):
    """The menu: for each page an icon with a label under it."""

    # Sizes at 100% display scaling; px() scales them where they are used.
    WIDTH = 100
    TOP_PAD = 16  # above the entry
    ICON_HEIGHT = 30
    PILL_WIDTH = 48  # the rounded shape behind an icon; its height is ICON_HEIGHT
    LABEL_GAP = 4  # between the icon and the label
    ENTRY_HEIGHT = 68  # from the top of one entry to the top of the next
    BOTTOM_PAD = 10  # below the last entry

    def __init__(self, parent: tk.Misc, selected: str, on_select: Callable[[str], None]) -> None:
        # No focus ring and no border: Tk adds both to a canvas.
        super().__init__(parent, width=px(self.WIDTH), bg=theme.MANTLE, highlightthickness=0, bd=0)
        self._selected = selected  # the key of the selected entry
        self._on_select = on_select  # called with the key when the user selects another entry
        self._hovered: str | None = None  # the key of the entry under the pointer
        self._pressed: str | None = None  # the key of the entry the button went down on
        self._entry_tops: dict[str, int] = {}  # key -> the top edge of the entry
        self._selected_pill = self._render_pill(theme.ACCENT_TINT)
        self._hovered_pill = self._render_pill(theme.SURFACE)
        self._bind_events()

    def _bind_events(self) -> None:
        self.bind("<Configure>", self._on_resize)
        # <Enter> too: the pointer can come in and stop, with no <Motion> after it.
        self.bind("<Enter>", self._on_mouse_move)
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_resize(self, event: tk.Event[tk.Canvas]) -> None:
        """Tk calls this when the menu appears and when its size changes."""
        self._draw(event.height)

    def _on_mouse_move(self, event: tk.Event[tk.Canvas]) -> None:
        self._set_hovered_entry(self._get_entry_at(event.y))

    def _on_mouse_leave(self, event: tk.Event[tk.Canvas]) -> None:
        self._set_hovered_entry(None)

    def _on_mouse_down(self, event: tk.Event[tk.Canvas]) -> None:
        self._pressed = self._get_entry_at(event.y)

    def _on_mouse_up(self, event: tk.Event[tk.Canvas]) -> None:
        """Select the entry if the button went down and up on it, like a normal button."""
        # after a drag the button can go up outside the menu
        is_inside: bool = 0 <= event.x < self.winfo_width()
        key = self._get_entry_at(event.y)
        if is_inside and key is not None and key == self._pressed:
            self._select(key)
        self._pressed = None

    def _render_pill(self, colour: str) -> tk.PhotoImage:
        """The rounded shape behind an icon, as an image in the given colour."""
        height = px(self.ICON_HEIGHT)
        return rounded_image(
            self,
            width=px(self.PILL_WIDTH),
            height=height,
            radius=height // 2,
            colour=colour,
            background=theme.MANTLE,  # the menu's background: the smooth edges blend into it
        )

    def _draw(self, height: int) -> None:
        """Draw the entries: two at the top edge and two at the bottom edge."""
        self.delete("all")
        top = px(self.TOP_PAD)
        bottom = height - px(self.BOTTOM_PAD)
        entry_height = px(self.ENTRY_HEIGHT)
        self._entry_tops = {
            "mirrors": top,
            "shortcuts": top + entry_height,
            "about": bottom - 2 * entry_height,
            "settings": bottom - entry_height,
        }
        for key, entry_top in self._entry_tops.items():
            self._draw_entry(key, entry_top)

    def _get_entry_look(self, key: str) -> tuple[tk.PhotoImage | None, str, str]:
        """How the entry looks now: (rounded shape or None, icon colour, label colour)."""
        if key == self._selected:
            return self._selected_pill, theme.ACCENT, theme.TEXT
        elif key == self._hovered:
            return self._hovered_pill, theme.TEXT, theme.TEXT
        else:
            return None, theme.SUBTEXT, theme.SUBTEXT

    def _draw_entry(self, key: str, top: int) -> None:
        """Draw one entry of ENTRIES. `top` is the entry's top edge."""
        icon, label = ENTRIES[key]
        pill, icon_colour, label_colour = self._get_entry_look(key)
        # start icon positions
        position_x = px(self.WIDTH) // 2
        position_y = top + px(self.ICON_HEIGHT) // 2
        # label position from top
        label_y = position_y + px(self.ICON_HEIGHT) // 2 + px(self.LABEL_GAP)
        # draw the rounded shape behind the icon
        if pill is not None:
            self.create_image(position_x, position_y, image=pill)
        # draw icon
        self.create_text(
            position_x,
            position_y,
            text=icon,
            font=theme.FONT_ICON_LARGE,
            fill=icon_colour,
        )
        # draw text
        self.create_text(
            position_x,
            label_y,
            text=tr(label),
            anchor="n",
            font=theme.FONT_CAPTION,
            fill=label_colour,
        )

    def _get_entry_at(self, position_y: int) -> str | None:
        """The key of the entry at `position_y`, or None for the empty space.

        `position_y` is the mouse "y" position on the menu.
        An entry reacts in a band: the full width of the menu, ENTRY_HEIGHT high.
        """
        for key, top in self._entry_tops.items():
            if top <= position_y < top + px(self.ENTRY_HEIGHT):
                return key
        return None

    def _set_hovered_entry(self, key: str | None) -> None:
        if key == self._hovered:
            return
        self._hovered = key
        self._update_pointer()
        self._draw(self.winfo_height())

    def _select(self, key: str) -> None:
        if key == self._selected:
            return
        self._selected = key
        self._update_pointer()
        self._draw(self.winfo_height())
        self._on_select(key)

    def _update_pointer(self) -> None:
        """Show a hand over an entry that can be clicked."""
        # the selected entry is already open, so it is not clickable
        is_clickable: bool = self._hovered is not None and self._hovered != self._selected
        self.configure(cursor="hand2" if is_clickable else "")
