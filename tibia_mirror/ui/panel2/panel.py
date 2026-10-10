"""The panel: everything inside the main window."""

import tkinter as tk

from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.nav import NavRail

# Sizes at 100% display scaling; px() scales them where they are used.
SIDE_PAD = 20  # left and right of the content
CONNECTION_TOP_PAD = 14  # above the connection line


class Panel(tk.Frame):
    """Everything inside the main window."""

    def __init__(self, root: tk.Misc) -> None:
        super().__init__(root, bg=theme.BG)
        self._add_menu()
        self._add_content()
        self._add_connection_line()

    def _add_menu(self) -> None:
        NavRail(self).pack(side="left", fill="y")

    def _add_content(self) -> None:
        """The area to the right of the menu. It takes all the space the menu leaves."""
        self._content = tk.Frame(self, bg=theme.BG)
        self._content.pack(side="left", fill="both", expand=True)

    def _add_connection_line(self) -> None:
        """The line at the top that says if the app has found Tibia."""
        self._connection = tk.Label(
            self._content,
            text="● " + tr("Waiting for Tibia..."),
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT,
        )
        self._connection.pack(
            side="top",
            anchor="w",
            padx=px(SIDE_PAD),
            pady=(px(CONNECTION_TOP_PAD), 0),
        )
