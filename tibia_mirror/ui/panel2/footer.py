"""The footer at the bottom of the panel: the tip text and the credit."""

import tkinter as tk
from datetime import date

from tibia_mirror.about import AUTHOR, TIP_CHARACTER, copyright_years
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.widgets import CopyText

# At 100% display scaling; px() scales it where it is used.
TIP_DIVIDER_PAD = 10  # above and below the thin line between the tip and the credit

# A tk.Label starts its text 3 pixels from its left edge (border and padding).
# Tk does not scale those, so this is not scaled.
LABEL_INSET = 3


class Footer(tk.Frame):
    """The tip text and, under it, the credit. It is the same on every page."""

    def __init__(self, parent: tk.Misc, width: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width  # the width of the content, in pixels
        self._add_tip()
        self._add_credit()

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
            self,
            text=tr("Enjoying it?"),
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT_SMALL,
        )
        label.pack(side="top", anchor="w")

    def _add_tip_sentence(self) -> None:
        """The line "Tip a few Tibia Coins to", with the coins in gold."""
        self._tip_row = tk.Frame(self, bg=theme.BG)
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
        return self._width - LABEL_INSET - sentence_width

    def _add_tip_divider(self) -> None:
        """The thin line between the tip and the credit."""
        divider = tk.Frame(self, bg=theme.SURFACE_HI, height=px(1), width=self._width)
        divider.pack(side="top", anchor="w", pady=px(TIP_DIVIDER_PAD))

    def _add_credit(self) -> None:
        """Two small lines: the author and the license."""
        years = copyright_years(date.today().year)
        lines = (
            tr("Created by {author}", author=AUTHOR),
            # The name of the license is never translated.
            tr("© {years} · PolyForm Strict License", years=years),
        )
        for text in lines:
            label = tk.Label(self, text=text, bg=theme.BG, fg=theme.SUBTEXT, font=theme.FONT_SMALL)
            label.pack(side="top", anchor="w")
