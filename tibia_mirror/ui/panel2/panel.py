"""The panel: everything inside the main window."""

import tkinter as tk
from datetime import date

from tibia_mirror.about import AUTHOR, copyright_years
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.nav import NavRail

# Sizes at 100% display scaling; px() scales them where they are used.
SIDE_PAD = 20  # left and right of the content
CONNECTION_TOP_PAD = 14  # above the connection line
FOOTER_TOP_PAD = 10  # between the thin line and the footer's text
FOOTER_BOTTOM_PAD = 12  # below the footer's text


class Panel(tk.Frame):
    """Everything inside the main window."""

    def __init__(self, root: tk.Misc) -> None:
        super().__init__(root, bg=theme.BG)
        self._add_menu()
        self._add_content()
        self._add_connection_line()
        self._add_footer()
        self._add_credit()

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

    def _add_footer(self) -> None:
        """The area at the bottom, under a thin line. It is the same on every page."""
        self._footer = tk.Frame(self._content, bg=theme.BG)
        self._footer.pack(
            side="bottom",
            anchor="w",
            padx=px(SIDE_PAD),
            pady=(px(FOOTER_TOP_PAD), px(FOOTER_BOTTOM_PAD)),
        )
        # side="bottom" stacks upwards, so the thin line lands above the footer.
        thin_line = tk.Frame(self._content, bg=theme.SURFACE_HI, height=px(1))
        thin_line.pack(side="bottom", fill="x")

    def _add_credit(self) -> None:
        """Two small lines in the footer: the author and the license."""
        years = copyright_years(date.today().year)
        lines = (
            tr("Created by {author}", author=AUTHOR),
            # The name of the license is never translated.
            tr("© {years} · PolyForm Strict License", years=years),
        )
        for text in lines:
            label = tk.Label(
                self._footer, text=text, bg=theme.BG, fg=theme.SUBTEXT, font=theme.FONT_SMALL
            )
            label.pack(side="top", anchor="w")
