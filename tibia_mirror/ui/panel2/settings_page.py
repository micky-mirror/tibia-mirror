"""The Settings page: groups of settings, each under its own caption."""

import tkinter as tk

from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.widgets import ScrollList

# Sizes at 100% display scaling; px() scales them where they are used.
TOP_PAD = 8  # above the first line of the page
BOTTOM_PAD = 8  # below the last line of the page
CAPTION_TOP_PAD = 10  # above each caption
CAPTION_BOTTOM_PAD = 6  # between a caption and its group


class SettingsPage(tk.Frame):
    """The Settings page."""

    def __init__(self, parent: tk.Misc, width: int, side_pad: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width  # the width of the content, in pixels
        self._add_column(side_pad)
        self._add_caption(tr("GENERAL"))

    def _add_column(self, side_pad: int) -> None:
        """The column that holds the groups of the page, one under another.

        It scrolls when the window is too short to show the whole page.
        """
        scroll_list = ScrollList(self, width=self._width)
        scroll_list.pack(
            side="top",
            anchor="w",
            fill="y",
            expand=True,
            padx=(side_pad, 0),
            pady=(px(TOP_PAD), px(BOTTOM_PAD)),
        )
        self._column = scroll_list.inner

    def _add_caption(self, text: str) -> None:
        """The small grey title above one group of settings."""
        caption = tk.Label(
            self._column,
            text=text,
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT_CAPTION,
        )
        caption.pack(
            side="top",
            anchor="w",
            pady=(px(CAPTION_TOP_PAD), px(CAPTION_BOTTOM_PAD)),
        )
