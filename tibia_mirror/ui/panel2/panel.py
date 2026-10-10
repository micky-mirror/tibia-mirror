"""The panel: everything inside the main window."""

import tkinter as tk

from tibia_mirror.config import PANEL_SIZE
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.about_page import AboutPage
from tibia_mirror.ui.panel2.footer import Footer
from tibia_mirror.ui.panel2.nav import NavRail

# Sizes at 100% display scaling; px() scales them where they are used.
SIDE_PAD = 20  # left and right of the content
CONNECTION_TOP_PAD = 14  # above the connection line
FOOTER_TOP_PAD = 10  # between the thin line and the footer
FOOTER_BOTTOM_PAD = 12  # below the footer


def content_width() -> int:
    """The width of the content: the normal window width without the menu and the side space.

    It is fixed. A wider window leaves empty space on the right.
    """
    return px(PANEL_SIZE[0]) - px(NavRail.WIDTH) - 2 * px(SIDE_PAD)


class Panel(tk.Frame):
    """Everything inside the main window."""

    def __init__(self, root: tk.Misc) -> None:
        super().__init__(root, bg=theme.BG)
        self._add_menu()
        self._add_content()
        self._add_connection_line()
        self._add_footer()
        self._add_about_page()

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
        """The footer at the bottom, under a thin line."""
        footer = Footer(self._content, content_width())
        footer.pack(
            side="bottom",
            anchor="w",
            padx=px(SIDE_PAD),
            pady=(px(FOOTER_TOP_PAD), px(FOOTER_BOTTOM_PAD)),
        )
        # side="bottom" stacks upwards, so the thin line lands above the footer.
        thin_line = tk.Frame(self._content, bg=theme.SURFACE_HI, height=px(1))
        thin_line.pack(side="bottom", fill="x")

    def _add_about_page(self) -> None:
        self._about_page = AboutPage(self._content, px(SIDE_PAD))
        # Packed last, so the page gets the space between the connection line and the footer.
        self._about_page.pack(side="top", fill="both", expand=True)
