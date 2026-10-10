"""The panel: everything inside the main window."""

import tkinter as tk
from datetime import date

from tibia_mirror.about import AUTHOR, TIP_CHARACTER, copyright_years
from tibia_mirror.config import PANEL_SIZE
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.widgets import CopyText
from tibia_mirror.ui.panel2.nav import NavRail

# Sizes at 100% display scaling; px() scales them where they are used.
SIDE_PAD = 20  # left and right of the content
CONNECTION_TOP_PAD = 14  # above the connection line
FOOTER_TOP_PAD = 10  # between the thin line and the footer's text
FOOTER_BOTTOM_PAD = 12  # below the footer's text
TIP_DIVIDER_PAD = 10  # above and below the thin line between the tip and the credit

# A tk.Label starts its text 3 pixels from its left edge (border and padding).
# Tk does not scale those, so this is not scaled.
LABEL_INSET = 3


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
        self._add_tip()
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

    def _add_tip(self) -> None:
        """The tip text above the credit, with a thin line between them.

        TIP_CHARACTER can be None; then the footer shows only the credit.
        """
        if TIP_CHARACTER is None:
            return
        self._add_tip_question()
        self._add_tip_sentence()
        self._add_tip_name(TIP_CHARACTER)
        self._add_tip_divider()

    def _add_tip_question(self) -> None:
        label = tk.Label(
            self._footer,
            text=tr("Enjoying it?"),
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT_SMALL,
        )
        label.pack(side="top", anchor="w")

    def _add_tip_sentence(self) -> None:
        """The line "Tip a few Tibia Coins to", with the coins in gold."""
        self._tip_row = tk.Frame(self._footer, bg=theme.BG)
        # The row starts where the text of the label above starts.
        self._tip_row.pack(side="top", anchor="w", padx=(LABEL_INSET, 0))
        before, after = tr("Tip {coins} to").split("{coins}")
        self._add_tip_words(before, theme.SUBTEXT)
        self._add_tip_words(tr("a few Tibia Coins"), theme.GOLD)
        self._add_tip_words(after + " ", theme.SUBTEXT)

    def _add_tip_words(self, text: str, colour: str) -> None:
        """One piece of the tip sentence, in its own colour."""
        # No border and no padding, so the pieces touch like words in one sentence.
        label = tk.Label(
            self._tip_row, text=text, bg=theme.BG, fg=colour, font=theme.FONT_SMALL, bd=0, padx=0
        )
        label.pack(side="left")

    def _add_tip_name(self, character: str) -> None:
        """The character to tip, in gold, at the end of the tip sentence. A click copies it."""
        name = CopyText(
            self._tip_row,
            character,
            background=theme.BG,
            fg=theme.GOLD,
            small=True,
            inset=0,
            max_width=self._tip_name_space(),
        )
        name.pack(side="left")

    def _tip_name_space(self) -> int:
        """The width left for the name after the sentence. A longer name is cut short."""
        sentence_width = sum(words.winfo_reqwidth() for words in self._tip_row.winfo_children())
        return content_width() - LABEL_INSET - sentence_width

    def _add_tip_divider(self) -> None:
        """The thin line between the tip and the credit."""
        divider = tk.Frame(self._footer, bg=theme.SURFACE_HI, height=px(1), width=content_width())
        divider.pack(side="top", anchor="w", pady=px(TIP_DIVIDER_PAD))

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
