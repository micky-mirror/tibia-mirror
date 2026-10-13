"""The panel: everything inside the main window."""

import tkinter as tk

from tibia_mirror.config import PANEL_SIZE
from tibia_mirror.i18n import tr
from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.about_page import AboutPage
from tibia_mirror.ui.panel2.footer import Footer
from tibia_mirror.ui.panel2.mirrors_page import MirrorsPage
from tibia_mirror.ui.panel2.nav import NavRail
from tibia_mirror.ui.panel2.settings_page import SettingsPage
from tibia_mirror.ui.panel2.shortcuts_page import ShortcutsPage

# Sizes at 100% display scaling; px() scales them where they are used.
SIDE_PAD = 20  # left and right of the content
CONNECTION_TOP_PAD = 14  # above the connection line
FOOTER_TOP_PAD = 10  # between the thin line and the footer
FOOTER_BOTTOM_PAD = 12  # below the footer

START_PAGE = "mirrors"  # the page that is open when the app starts

# The states of the connection to Tibia.
WAITING = "waiting"  # Tibia is not found yet
MINIMIZED = "minimized"  # Tibia is found, but it is minimized
CONNECTED = "connected"  # Tibia is found and its window is open

# The texts of the connection line: state -> text in English.
CONNECTION_TEXTS = {
    WAITING: "Waiting for Tibia...",
    MINIMIZED: "Tibia is minimized",
    CONNECTED: "Tibia connected",
}


def content_width() -> int:
    """The width of the content: the normal window width without the menu and the side space.

    It is fixed. A wider window leaves empty space on the right.
    """
    return px(PANEL_SIZE[0]) - px(NavRail.WIDTH) - 2 * px(SIDE_PAD)


class Panel(tk.Frame):
    """Everything inside the main window."""

    def __init__(
        self,
        root: tk.Misc,
        settings: AppSettingsStore,
        start_page: str = START_PAGE,
    ) -> None:
        super().__init__(root, bg=theme.BG)
        self._settings = settings
        self.open_page = start_page  # the key of the page that is shown
        self._add_menu()
        self._add_content()
        self._add_connection_line()
        self._add_footer()
        self._add_pages()

    def _add_menu(self) -> None:
        NavRail(self, self.open_page, self._show_page).pack(side="left", fill="y")

    def _add_content(self) -> None:
        """The area to the right of the menu. It takes all the space the menu leaves."""
        self._content = tk.Frame(self, bg=theme.BG)
        self._content.pack(side="left", fill="both", expand=True)

    def _add_connection_line(self) -> None:
        """The line at the top that says if the app has found Tibia."""
        self._connection = tk.Label(self._content, bg=theme.BG, font=theme.FONT)
        self._connection.pack(
            side="top",
            anchor="w",
            padx=px(SIDE_PAD),
            pady=(px(CONNECTION_TOP_PAD), 0),
        )
        self.set_connection_state(WAITING)

    def set_connection_state(self, state: str) -> None:
        """Set Tibia connection state."""
        is_connected: bool = state == CONNECTED

        text = tr(CONNECTION_TEXTS[state])
        colour = theme.GREEN if is_connected else theme.SUBTEXT

        self._connection.configure(text="● " + text, fg=colour)

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

    def _add_pages(self) -> None:
        """Create every page and show the open one.

        The keys are the keys of the menu entries.
        """
        self._pages: dict[str, tk.Frame] = {
            "mirrors": MirrorsPage(self._content, content_width(), px(SIDE_PAD)),
            "shortcuts": ShortcutsPage(self._content, content_width(), px(SIDE_PAD)),
            "about": AboutPage(self._content, content_width(), px(SIDE_PAD)),
            "settings": SettingsPage(self._content, content_width(), px(SIDE_PAD), self._settings),
        }
        self._pack_page(self.open_page)

    def _show_page(self, key: str) -> None:
        """Show the page `key` in place of the open one. The menu calls this."""
        self._pages[self.open_page].pack_forget()  # hide currently displayed page
        self.open_page = key  # assign selected page
        self._pack_page(key)  # open selected page

    def _pack_page(self, key: str) -> None:
        # Packed last, so the page gets the space between the connection line and the footer.
        self._pages[key].pack(side="top", fill="both", expand=True)
