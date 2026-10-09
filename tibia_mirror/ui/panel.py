"""The control panel: the menu rail, connection status, the selected page and the footer.

Adding a page means a NavItem in SECTIONS and an entry in ControlPanel._pages.
"""

import tkinter as tk
import tkinter.font as tkfont
from datetime import date

from tibia_mirror.about import AUTHOR, TIP_CHARACTER, copyright_years
from tibia_mirror.config import PANEL_SIZE
from tibia_mirror.core.settings import Settings
from tibia_mirror.i18n import tr
from tibia_mirror.ui.about_page import build_about_page
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.widgets import CopyText
from tibia_mirror.ui.mirrors_page import MirrorsActions, MirrorsPage
from tibia_mirror.ui.nav import NavItem, NavRail
from tibia_mirror.ui.settings_page import OnChange, build_settings_page
from tibia_mirror.ui.shortcuts_page import build_shortcuts_page

PAD = 20
TIP_GAP = 10  # above and below the hairline between the footer's tip line and its credit


def content_width() -> int:
    """The content column: fixed width, anchored left; a wider panel leaves space on the right."""
    return px(PANEL_SIZE[0]) - px(NavRail.WIDTH) - 2 * px(PAD)


# Labels are English here and translated when the rail draws them.
SECTIONS = (
    NavItem("mirrors", "Mirrors", "\ue8b9"),
    NavItem("shortcuts", "Shortcuts", "\ue765"),
    NavItem("about", "About", "\ue946", pinned_bottom=True),
    NavItem("settings", "Settings", "\ue713", pinned_bottom=True),
)


class ControlPanel:
    """Pure view: every control forwards to a callback from the App.

    The App drives `mirrors` (the Mirrors page) directly. destroy() removes it all,
    so the App can rebuild it in a new theme or language on the same `page`.
    """

    def __init__(
        self,
        root: tk.Misc,
        settings: Settings,
        mirrors_actions: MirrorsActions,
        on_setting: OnChange,
        page: str = SECTIONS[0].key,
    ) -> None:
        width, pad = content_width(), px(PAD)
        self._frame = tk.Frame(root, bg=theme.BG)
        self._frame.pack(fill="both", expand=True)
        NavRail(self._frame, SECTIONS, page, self._show_page).pack(side="left", fill="y")
        body = tk.Frame(self._frame, bg=theme.BG)
        body.pack(side="left", fill="both", expand=True)

        # No title here: the window's title bar already says "Tibia Mirror".
        status = tk.Frame(body, bg=theme.BG)
        status.pack(anchor="w", padx=pad, pady=(px(14), 0))
        self._connection = tk.Label(status, bg=theme.BG, font=theme.FONT)
        self._connection.pack(side="left")
        self._all_hidden = tk.Label(status, bg=theme.BG, fg=theme.YELLOW, font=theme.FONT)

        # Packed before the pages, so it stays at the bottom of every one
        # (bottom-side packing stacks upwards).
        footer = tk.Frame(body, bg=theme.BG)
        footer.pack(side="bottom", anchor="w", padx=pad, pady=(px(10), px(12)))
        tk.Frame(body, bg=theme.SURFACE_HI, height=px(1)).pack(side="bottom", fill="x")
        if TIP_CHARACTER is not None:
            self._build_tip_line(footer, TIP_CHARACTER, width)
            # A hairline, with room around it, between the tip and the credit.
            tk.Frame(footer, bg=theme.SURFACE_HI, height=px(1), width=width).pack(
                anchor="w", pady=px(TIP_GAP)
            )
        for text in (
            tr("Created by {author}", author=AUTHOR),
            # The license's name is never translated.
            tr("© {years} · PolyForm Strict License", years=copyright_years(date.today().year)),
        ):
            tk.Label(footer, text=text, bg=theme.BG, fg=theme.SUBTEXT, font=theme.FONT_SMALL).pack(
                anchor="w"
            )

        self.mirrors = MirrorsPage(body, mirrors_actions, width=width, pad=pad)
        self._pages = {
            "mirrors": self.mirrors,
            "shortcuts": build_shortcuts_page(
                body, settings, width=width, pad=pad, on_change=on_setting
            ),
            "settings": build_settings_page(
                body, settings, width=width, pad=pad, on_change=on_setting
            ),
            "about": build_about_page(body, width=width, pad=pad),
        }
        self.page = page
        self._pages[page].pack(fill="both", expand=True)
        self.set_connection("waiting")

    @staticmethod
    def _build_tip_line(footer: tk.Frame, character: str, width: int) -> None:
        """The tip sentence in short, on two lines: coins and name in gold, the name copyable.

        A name too long for the line is cut short, but still copied in full.
        """
        tk.Label(
            footer, text=tr("Enjoying it?"), bg=theme.BG, fg=theme.SUBTEXT, font=theme.FONT_SMALL
        ).pack(anchor="w")
        inset = 3  # in line with the label above (a tk.Label's border and padding, never scaled)
        row = tk.Frame(footer, bg=theme.BG)
        row.pack(anchor="w", padx=(inset, 0))
        before, after = tr("Tip {coins} to").split("{coins}")
        font = tkfont.Font(font=theme.FONT_SMALL)
        used = inset
        for text, fg in (
            (before, theme.SUBTEXT),
            (tr("a few Tibia Coins"), theme.GOLD),
            (after + " ", theme.SUBTEXT),
        ):
            tk.Label(row, text=text, bg=theme.BG, fg=fg, font=theme.FONT_SMALL, bd=0, padx=0).pack(
                side="left"
            )
            used += font.measure(text)
        CopyText(
            row,
            character,
            background=theme.BG,
            fg=theme.GOLD,
            small=True,
            inset=0,
            max_width=width - used,
        ).pack(side="left")

    def destroy(self) -> None:
        self._frame.destroy()

    def _show_page(self, key: str) -> None:
        self._pages[self.page].pack_forget()
        self.page = key
        self._pages[key].pack(fill="both", expand=True)

    def set_connection(self, state: str) -> None:
        """Show the state: "waiting" (no Tibia yet), "minimized" or "connected"."""
        text, color = {
            "waiting": (tr("Waiting for Tibia..."), theme.SUBTEXT),
            "minimized": (tr("Tibia is minimized"), theme.SUBTEXT),
            "connected": (tr("Tibia connected"), theme.GREEN),
        }[state]
        self._connection.config(text="● " + text, fg=color)

    def set_all_hidden(self, key_name: str | None) -> None:
        """Say the hide-all key (`key_name`, e.g. "F12") has hidden every mirror; None clears it."""
        if key_name is None:
            self._all_hidden.pack_forget()
            return
        self._all_hidden.config(text=tr("Mirrors hidden ({key})", key=key_name))
        self._all_hidden.pack(side="left", padx=(px(12), 0))
