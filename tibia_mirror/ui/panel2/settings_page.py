"""The Settings page: groups of settings, each under its own caption."""

import tkinter as tk
from collections.abc import Sequence

from tibia_mirror.config import DEFAULT_OPACITY
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.widgets import ScrollList
from tibia_mirror.ui.panel2.choice_row import ChoiceRow
from tibia_mirror.ui.panel2.row import Row
from tibia_mirror.ui.panel2.settings_card import SettingsCard
from tibia_mirror.ui.panel2.slider_row import SliderRow
from tibia_mirror.ui.panel2.toggle_row import ToggleRow

# Sizes at 100% display scaling; px() scales them where they are used.
TOP_PAD = 8  # above the first line of the page
BOTTOM_PAD = 8  # below the last line of the page
CAPTION_TOP_PAD = 10  # above each caption
CAPTION_BOTTOM_PAD = 6  # between a caption and its group


def percent(value: float) -> str:
    """A part of one as a whole percent: 0.5 becomes "50%"."""
    return f"{round(value * 100)}%"


class SettingsPage(tk.Frame):
    """The Settings page."""

    def __init__(self, parent: tk.Misc, width: int, side_pad: int) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width  # the width of the content, in pixels
        self._add_column(side_pad)
        self._add_general_group()
        self._add_profiles_group()
        self._add_saving_group()
        self._add_mirrors_group()

    def _add_column(self, side_pad: int) -> None:
        """The column that holds the groups of the page, one under another.

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

    def _add_general_group(self) -> None:
        """The first group: settings of the app as a whole."""
        self._add_caption(tr("GENERAL"))
        # The names of languages are written in their own language, never translated.
        language_row = ChoiceRow(
            tr("Language"),
            (("en", "English"), ("pl", "Polski")),
            "en",
        )
        theme_row = ChoiceRow(
            tr("Theme"),
            (("dark", tr("Dark")), ("light", tr("Light"))),
            "dark",
        )
        on_top_row = ToggleRow(
            tr("Keep this panel on top"),
            tr("Stays above other windows."),
            is_on=False,
        )
        self._add_card([language_row, theme_row, on_top_row])

    def _add_profiles_group(self) -> None:
        """The second group: how the app chooses a profile."""
        self._add_caption(tr("PROFILES"))
        per_character_row = ToggleRow(
            tr("Profile per character"),
            tr("Logging in opens the character's profile, creating one the first time."),
            is_on=False,
        )
        self._add_card([per_character_row])

    def _add_saving_group(self) -> None:
        """The third group: when changes are saved."""
        self._add_caption(tr("SAVING"))
        autosave_row = ToggleRow(
            tr("Save automatically"),
            tr("Saves every change as you make it."),
            is_on=False,
        )
        self._add_card([autosave_row])

    def _add_mirrors_group(self) -> None:
        """The fourth group: how the mirrors look."""
        self._add_caption(tr("MIRRORS"))
        opacity_row = SliderRow(
            tr("Opacity of new mirrors"),
            tr("Each mirror can still be set on its card."),
            value=DEFAULT_OPACITY,
            value_text=percent,
        )
        self._add_card([opacity_row])

    def _add_caption(self, text: str) -> None:
        """The small grey title above one group of settings."""
        caption = tk.Label(
            self._column,
            text=text,
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT_CAPTION,
        )
        caption.pack(
            side="top",
            anchor="w",
            pady=(px(CAPTION_TOP_PAD), px(CAPTION_BOTTOM_PAD)),
        )

    def _add_card(self, rows: Sequence[Row]) -> None:
        """The rounded box under a caption, with the rows of one group."""
        card = SettingsCard(self._column, self._width, rows)
        card.pack(side="top", anchor="w")
