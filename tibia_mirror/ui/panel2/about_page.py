"""The About page: what the app is for, its version, contact, tips and the trademark notice."""

import tkinter as tk

from tibia_mirror import __version__
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px

# At 100% display scaling; px() scales it where it is used.
TOP_PAD = 18  # above the title


class AboutPage(tk.Frame):
    """The About page."""

    def __init__(self, parent: tk.Misc, side_pad: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._add_column(side_pad)
        self._add_title()
        self._add_version()

    def _add_column(self, side_pad: int) -> None:
        """The column that holds the lines of the page, one under another."""
        self._column = tk.Frame(self, bg=theme.BG)
        self._column.pack(side="top", anchor="w", padx=(side_pad, 0), pady=(px(TOP_PAD), 0))

    def _add_title(self) -> None:
        # The name of the app is never translated.
        title = tk.Label(
            self._column, text="Tibia Mirror", bg=theme.BG, fg=theme.TEXT, font=theme.FONT_TITLE
        )
        title.pack(side="top", anchor="w")

    def _add_version(self) -> None:
        version = tk.Label(
            self._column,
            text=tr("Version {version}", version=__version__),
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT,
        )
        version.pack(side="top", anchor="w")
