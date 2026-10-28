"""The About page: what the app is for, its version, contact, tips and the trademark notice."""

import tkinter as tk
from collections.abc import Sequence

from tibia_mirror import __version__
from tibia_mirror.about import DISCORD, TIP_CHARACTER
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.copy_text import CopyText
from tibia_mirror.ui.panel.controls.rich_paragraph import RichParagraph
from tibia_mirror.ui.panel.controls.scroll_list import ScrollList

# Sizes at 100% display scaling; px() scales them where they are used.
TOP_PAD = 18  # above the title
PARAGRAPH_GAP = 14  # above each paragraph
BOTTOM_PAD = 8  # below the last line of the page


class AboutPage(tk.Frame):
    """The About page."""

    def __init__(self, parent: tk.Misc, width: int, side_pad: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width  # the width of the content, in pixels
        self._add_column(side_pad)
        self._add_title()
        self._add_version()
        self._add_intro()
        self._add_contact()
        self._add_tip()
        self._add_trademark_notice()

    def _add_column(self, side_pad: int) -> None:
        """The column that holds the lines of the page, one under another.

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

    def _add_intro(self) -> None:
        """Two paragraphs: what the app is for, and how it works."""
        self._add_paragraph(
            tr(
                "Keep your eyes on the fight, not on the corners of the screen. "
                "Tibia Mirror puts the parts of Tibia you care about - cooldowns, "
                "the minimap, anything you like - into small windows you can place "
                "wherever suits you."
            ),
            theme.TEXT,
        )
        self._add_paragraph(
            tr(
                "It uses Windows' own window previews - the same ones you see on the taskbar. "
                "No screen capture, nothing changed in the game, nothing sent anywhere."
            ),
            theme.TEXT,
        )

    def _add_contact(self) -> None:
        """How to reach the author: a sentence, and under it the Discord name to copy.

        DISCORD can be None; then the page has no contact part.
        """
        if DISCORD is None:
            return
        self._add_contact_sentence()
        self._add_copy_name(DISCORD, theme.BLURPLE)

    def _add_contact_sentence(self) -> None:
        """The sentence that sends the reader to Discord, with "Discord" in its own colour."""
        before, after = tr("Questions or ideas? Message me on {discord}:").split("{discord}")
        text_parts = [(before, theme.TEXT), (tr("Discord"), theme.BLURPLE), (after, theme.TEXT)]
        self._add_rich_paragraph(text_parts)

    def _add_tip(self) -> None:
        """How to say thanks: a sentence, and under it the character name to copy.

        TIP_CHARACTER can be None; then the page has no tip part.
        """
        if TIP_CHARACTER is None:
            return
        self._add_tip_sentence()
        self._add_copy_name(TIP_CHARACTER, theme.GOLD)

    def _add_tip_sentence(self) -> None:
        """The sentence that says the app is free, with the coins in gold."""
        sentence = tr(
            "Tibia Mirror is free. If you find it useful, you can say thanks "
            "by sending {coins} to this character:"
        )
        before, after = sentence.split("{coins}")
        coins = tr("a few Tibia Coins")
        text_parts = [(before, theme.TEXT), (coins, theme.GOLD), (after, theme.TEXT)]
        self._add_rich_paragraph(text_parts)

    def _add_copy_name(self, name: str, colour: str) -> None:
        """A name on its own line, with a copy icon. A click copies the name."""
        copy_name = CopyText(self._column, name, text_colour=colour, background=theme.BG)
        copy_name.pack(side="top", anchor="w")

    def _add_trademark_notice(self) -> None:
        """The last paragraph: the app is made by a fan and is not a CipSoft product."""
        self._add_paragraph(
            tr(
                "A fan-made tool for the Tibia community. Tibia is a trademark of "
                "CipSoft GmbH, and this app is not affiliated with or endorsed by CipSoft."
            ),
            theme.SUBTEXT,
        )

    def _add_paragraph(self, text: str, colour: str) -> None:
        """One paragraph of text. Long lines break at the width of the content."""
        paragraph = tk.Label(
            self._column,
            text=text,
            bg=theme.BG,
            fg=colour,
            font=theme.FONT,
            justify="left",
            wraplength=self._width,
        )
        paragraph.pack(side="top", anchor="w", pady=(px(PARAGRAPH_GAP), 0))

    def _add_rich_paragraph(self, text_parts: Sequence[tuple[str, str]]) -> None:
        """One paragraph where each part has its own colour: a list of (text, colour)."""
        paragraph = RichParagraph(self._column, text_parts, self._width)
        paragraph.pack(side="top", anchor="w", pady=(px(PARAGRAPH_GAP), 0))
