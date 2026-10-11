"""The Shortcuts page: keys that act on the mirrors while Tibia is active."""

import tkinter as tk

from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.panel2.scroll_cards import ScrollCards


class ShortcutsPage(tk.Frame):
    """The Shortcuts page."""

    def __init__(self, parent: tk.Misc, width: int, side_pad: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width
        self._side_pad = side_pad
        # initialize scrollable card
        self._add_scroll_cards()
        # add card blocks to scrollable card
        self._add_mirrors_group()

    def _add_scroll_cards(self) -> None:
        """The scrolling column that holds the groups of the page."""
        self._scroll_cards = ScrollCards(self, self._width, self._side_pad)
        self._scroll_cards.pack(side="top", fill="both", expand=True)

    def _add_mirrors_group(self) -> None:
        """The only group: keys that act on all mirrors at once."""
        self._scroll_cards.add_caption(tr("MIRRORS"))
