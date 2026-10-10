"""The menu on the left side of the panel."""

import tkinter as tk

from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
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
    LABEL_GAP = 4  # between the icon and the label
    ENTRY_HEIGHT = 68  # from the top of one entry to the top of the next
    BOTTOM_PAD = 10  # below the last entry

    def __init__(self, parent: tk.Misc) -> None:
        # No focus ring and no border: Tk adds both to a canvas.
        super().__init__(parent, width=px(self.WIDTH), bg=theme.MANTLE, highlightthickness=0, bd=0)
        self._selected = "mirrors"  # the key of the selected entry; Mirrors at the start
        # Tk sends <Configure> when the menu appears and when its size changes.
        self.bind("<Configure>", lambda event: self._draw(event.height))

    def _draw(self, height: int) -> None:
        """Draw the entries: two at the top edge and two at the bottom edge."""
        self.delete("all")
        top = px(self.TOP_PAD)
        bottom = height - px(self.BOTTOM_PAD)
        entry_height = px(self.ENTRY_HEIGHT)
        self._draw_entry("mirrors", top)
        self._draw_entry("shortcuts", top + entry_height)
        self._draw_entry("about", bottom - 2 * entry_height)
        self._draw_entry("settings", bottom - entry_height)

    def _draw_entry(self, key: str, top: int) -> None:
        """Draw one entry of ENTRIES. `top` is the entry's top edge."""
        icon, label = ENTRIES[key]
        # start icon positions
        position_x = px(self.WIDTH) // 2
        position_y = top + px(self.ICON_HEIGHT) // 2
        # label position from top
        label_y = position_y + px(self.ICON_HEIGHT) // 2 + px(self.LABEL_GAP)
        # colours: the selected entry is brighter
        is_selected: bool = key == self._selected

        icon_colour = theme.ACCENT if is_selected else theme.SUBTEXT
        label_colour = theme.TEXT if is_selected else theme.SUBTEXT
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
