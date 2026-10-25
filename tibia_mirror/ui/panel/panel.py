"""The panel: everything inside the main window."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Sequence

from tibia_mirror.app_parts.profile_manager import ProfileManager
from tibia_mirror.config import PANEL_SIZE
from tibia_mirror.core.connection import CONNECTED, MINIMIZED, WAITING
from tibia_mirror.i18n import tr
from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import elide
from tibia_mirror.ui.panel.footer import Footer
from tibia_mirror.ui.panel.mirrors.mirror_info import MirrorInfo
from tibia_mirror.ui.panel.nav import NavRail
from tibia_mirror.ui.panel.pages.about_page import AboutPage
from tibia_mirror.ui.panel.pages.mirrors_page import MirrorsPage
from tibia_mirror.ui.panel.pages.settings_page import SettingsPage
from tibia_mirror.ui.panel.pages.shortcuts_page import ShortcutsPage
from tibia_mirror.ui.panel.profiles.profile_info import ProfileInfo

# Sizes at 100% display scaling; px() scales them where they are used.
SIDE_PAD = 20  # left and right of the content
CONNECTION_TOP_PAD = 14  # above the connection line
NOTE_GAP = 12  # between the connection text and the note about hidden mirrors
MESSAGE_GAP = 12  # at least this much between the texts on the left and the message
FOOTER_TOP_PAD = 10  # between the thin line and the footer
FOOTER_BOTTOM_PAD = 12  # below the footer

START_PAGE = "mirrors"  # the page that is open when the app starts

# The texts of the connection line: state -> text in English.
CONNECTION_TEXTS = {
    WAITING: "Waiting for Tibia...",
    MINIMIZED: "Tibia is minimized",
    CONNECTED: "Tibia connected",
}

# The colours of the message line: tone -> theme colour name.
MESSAGE_TONES = {"muted": "SUBTEXT", "ok": "GREEN", "error": "RED"}


def content_width() -> int:
    """The width of the content: the normal window width without the menu and the side space.

    It is fixed. A wider window leaves empty space on the right.
    """
    return px(PANEL_SIZE[0]) - px(NavRail.WIDTH) - 2 * px(SIDE_PAD)


class Panel(tk.Frame):
    """Everything inside the main window."""

    def __init__(
        self,
        window: tk.Misc,
        settings: AppSettingsStore,
        profile_manager: ProfileManager,
        connection_state: str,
        profile_info: ProfileInfo,
        on_profile_selected: Callable[[str], None],
        on_new_profile: Callable[[str], None],
        on_duplicate_profile: Callable[[str], None],
        on_rename_profile: Callable[[str], None],
        on_delete_profile: Callable[[], None],
        mirrors: Sequence[MirrorInfo] | None,
        on_mirror_changed: Callable[[MirrorInfo], None],
        on_mirror_removed: Callable[[str], None],
        on_select_area: Callable[[str | None], None],
    ) -> None:
        super().__init__(window, bg=theme.BG)
        self._settings = settings
        self._profile_manager = profile_manager
        self._connection_state = connection_state  # the state the connection line shows
        self._profile_info = profile_info
        self._on_profile_selected = on_profile_selected  # gets the name picked in the menu
        self._on_new_profile = on_new_profile  # gets the name typed for a new profile
        self._on_duplicate_profile = on_duplicate_profile  # gets the name typed for the copy
        self._on_rename_profile = on_rename_profile  # gets the new name typed for the profile
        self._on_delete_profile = on_delete_profile  # called when the user confirms the delete
        self._mirrors = mirrors
        self._on_mirror_changed = on_mirror_changed  # gets the new info after a card changed it
        self._on_mirror_removed = on_mirror_removed  # gets the mirror id after a card removed it
        # gets the id of the mirror whose area is selected again, None for a new mirror
        self._on_select_area = on_select_area
        self._open_page = START_PAGE  # the key of the page that is shown
        self._add_menu()
        self._add_content()
        self._add_top_line()
        self._add_footer()
        self._add_pages()

    def _add_menu(self) -> None:
        NavRail(self, self._open_page, self._show_page).pack(side="left", fill="y")

    def _add_content(self) -> None:
        """The area to the right of the menu. It takes all the space the menu leaves."""
        self._content = tk.Frame(self, bg=theme.BG)
        self._content.pack(side="left", fill="both", expand=True)

    def _add_top_line(self) -> None:
        """The line at the top: the connection on the left, a message on the right."""
        top_line = tk.Frame(self._content, bg=theme.BG)
        top_line.pack(
            side="top",
            fill="x",
            padx=px(SIDE_PAD),
            pady=(px(CONNECTION_TOP_PAD), 0),
        )
        self._add_connection_text(top_line)
        self._add_hidden_note(top_line)
        self._add_message(top_line)

    def _add_connection_text(self, top_line: tk.Frame) -> None:
        """The text that says if the app has found Tibia."""
        self._connection = tk.Label(top_line, bg=theme.BG, font=theme.FONT)
        self._connection.pack(side="left")
        self.set_connection_state(self._connection_state)

    def _add_hidden_note(self, top_line: tk.Frame) -> None:
        """A yellow note after the connection text. Shown only while the mirrors are hidden."""
        self._hidden_note = tk.Label(top_line, bg=theme.BG, fg=theme.YELLOW, font=theme.FONT)

    def _add_message(self, top_line: tk.Frame) -> None:
        """A short message for the user, on the right. Empty until set_message() is called."""
        self._message = tk.Label(top_line, bg=theme.BG, font=theme.FONT)
        self._message.place(relx=1.0, rely=0.5, anchor="e")
        self._message_font = tkfont.Font(font=theme.FONT)
        self._message_text = ""  # the whole text, before it is cut short to fit
        self._message_tone = "muted"

    def set_connection_state(self, state: str) -> None:
        """Set Tibia connection state."""
        self._connection_state = state
        is_connected: bool = state == CONNECTED

        text = tr(CONNECTION_TEXTS[state])
        colour = theme.GREEN if is_connected else theme.SUBTEXT

        self._connection.configure(text="● " + text, fg=colour)

    def set_profile_info(self, profile_info: ProfileInfo) -> None:
        """Show another active profile on the Mirrors page."""
        self._mirrors_page.set_profile_info(profile_info)

    def set_mirrors(self, mirrors: Sequence[MirrorInfo] | None) -> None:
        """Show these mirrors on the Mirrors page."""
        self._mirrors_page.set_mirrors(mirrors)

    def set_message(self, text: str, tone: str = "muted") -> None:
        """Show a short message for the user. An empty text hides it."""
        self._message_text = text
        self._message_tone = tone
        self._draw_message()

    def set_all_hidden(self, key_name: str | None) -> None:
        """Say that the hide-all key `key_name` hides every mirror. None takes the note away."""
        if key_name is None:
            self._hidden_note.pack_forget()
        else:
            self._hidden_note.configure(text=tr("Mirrors hidden ({key})", key=key_name))
            self._hidden_note.pack(side="left", padx=(px(NOTE_GAP), 0))

        # the message gets the space that is left
        self._draw_message()

    def _draw_message(self) -> None:
        """The message, cut short with "…" when it does not fit after the texts on the left."""
        free_width = content_width() - self._get_left_width() - px(MESSAGE_GAP)
        text = elide(self._message_text, self._message_font, free_width)
        colour = getattr(theme, MESSAGE_TONES[self._message_tone])

        self._message.configure(text=text, fg=colour)

    def _get_left_width(self) -> int:
        """The width of the connection text, and of the note about hidden mirrors."""
        left_width = self._connection.winfo_reqwidth()

        # the note is packed only while the mirrors are hidden
        if self._hidden_note.winfo_manager():
            left_width += px(NOTE_GAP) + self._hidden_note.winfo_reqwidth()

        return left_width

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
        self._mirrors_page = MirrorsPage(
            self._content,
            content_width(),
            px(SIDE_PAD),
            self._profile_info,
            self._on_profile_selected,
            self._on_new_profile,
            self._on_duplicate_profile,
            self._on_rename_profile,
            self._on_delete_profile,
            self._mirrors,
            self._on_mirror_changed,
            self._on_mirror_removed,
            self._on_select_area,
        )
        self._pages: dict[str, tk.Frame] = {
            "mirrors": self._mirrors_page,
            "shortcuts": ShortcutsPage(
                self._content,
                content_width(),
                px(SIDE_PAD),
                self._settings,
                self._profile_manager,
            ),
            "about": AboutPage(self._content, content_width(), px(SIDE_PAD)),
            "settings": SettingsPage(self._content, content_width(), px(SIDE_PAD), self._settings),
        }
        self._pack_page(self._open_page)

    def _show_page(self, key: str) -> None:
        """Show the page `key` in place of the open one. The menu calls this."""
        self._pages[self._open_page].pack_forget()  # hide currently displayed page
        self._open_page = key  # assign selected page
        self._pack_page(key)  # open selected page

    def _pack_page(self, key: str) -> None:
        # Packed last, so the page gets the space between the connection line and the footer.
        self._pages[key].pack(side="top", fill="both", expand=True)
