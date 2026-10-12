"""The Settings page: groups of settings, each under its own caption."""

import tkinter as tk

from tibia_mirror.config import MIN_OPACITY, OPACITY_STEP
from tibia_mirror.i18n import tr
from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.text import percent
from tibia_mirror.ui.panel2.choice_row import ChoiceRow
from tibia_mirror.ui.panel2.scroll_cards import ScrollCards
from tibia_mirror.ui.panel2.slider_row import SliderRow
from tibia_mirror.ui.panel2.toggle_row import ToggleRow


class SettingsPage(tk.Frame):
    """The Settings page."""

    def __init__(
        self, parent: tk.Misc, width: int, side_pad: int, settings: AppSettingsStore
    ) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width
        self._side_pad = side_pad
        self._settings = settings
        # initialize scrollable card
        self._add_scroll_cards()
        # add card blocks to scrollable card
        self._add_general_group()
        self._add_profiles_group()
        self._add_saving_group()
        self._add_mirrors_group()

    def _add_scroll_cards(self) -> None:
        """The scrolling column that holds the groups of the page."""
        self._scroll_cards = ScrollCards(self, self._width, self._side_pad)
        self._scroll_cards.pack(side="top", fill="both", expand=True)

    def _add_general_group(self) -> None:
        """The first group: settings of the app as a whole."""
        current_settings = self._settings.current

        self._scroll_cards.add_caption(tr("GENERAL"))
        # The names of languages are written in their own language, never translated.
        language_row = ChoiceRow(
            tr("Language"),
            (("en", "English"), ("pl", "Polski")),
            current_settings.language,
        )
        theme_row = ChoiceRow(
            tr("Theme"),
            (("dark", tr("Dark")), ("light", tr("Light"))),
            current_settings.theme,
        )
        on_top_row = ToggleRow(
            tr("Keep this panel on top"),
            tr("Stays above other windows."),
            is_on=current_settings.is_panel_on_top,
            on_change=lambda is_on: self._settings.update(is_panel_on_top=is_on),
        )
        self._scroll_cards.add_card([language_row, theme_row, on_top_row])

    def _add_profiles_group(self) -> None:
        """The second group: how the app chooses a profile."""
        current_settings = self._settings.current

        self._scroll_cards.add_caption(tr("PROFILES"))
        per_character_row = ToggleRow(
            tr("Profile per character"),
            tr("Logging in opens the character's profile, creating one the first time."),
            is_on=current_settings.is_profile_per_character_on,
            on_change=lambda is_on: self._settings.update(is_profile_per_character_on=is_on),
        )
        self._scroll_cards.add_card([per_character_row])

    def _add_saving_group(self) -> None:
        """The third group: when changes are saved."""
        current_settings = self._settings.current

        self._scroll_cards.add_caption(tr("SAVING"))
        autosave_row = ToggleRow(
            tr("Save automatically"),
            tr("Saves every change as you make it."),
            is_on=current_settings.is_autosave_on,
            on_change=lambda is_on: self._settings.update(is_autosave_on=is_on),
        )
        self._scroll_cards.add_card([autosave_row])

    def _add_mirrors_group(self) -> None:
        """The fourth group: how the mirrors look."""
        current_settings = self._settings.current

        self._scroll_cards.add_caption(tr("MIRRORS"))
        opacity_row = SliderRow(
            tr("Opacity of new mirrors"),
            tr("Each mirror can still be set on its card."),
            value=current_settings.new_mirror_opacity,
            start=0.0,
            end=1.0,
            step=OPACITY_STEP,
            lowest=MIN_OPACITY,
            value_text=percent,
        )
        frame_row = ToggleRow(
            tr("Mirror frame"),
            tr("Grey outline on mirrors without a colour."),
            is_on=current_settings.is_mirror_frame_on,
            on_change=lambda is_on: self._settings.update(is_mirror_frame_on=is_on),
        )
        tint_row = ToggleRow(
            tr("Tint with frame colour"),
            tr("Shades coloured mirrors in their colour."),
            is_on=current_settings.is_frame_tint_on,
            on_change=lambda is_on: self._settings.update(is_frame_tint_on=is_on),
        )
        corners_row = ToggleRow(
            tr("Rounded corners"),
            tr("Clips a few pixels at each corner."),
            is_on=current_settings.is_rounded_corners_on,
            on_change=lambda is_on: self._settings.update(is_rounded_corners_on=is_on),
        )
        fades_row = ToggleRow(
            tr("Fade animations"),
            tr("Off: mirrors appear and hide instantly."),
            is_on=current_settings.is_fade_on,
            on_change=lambda is_on: self._settings.update(is_fade_on=is_on),
        )
        self._scroll_cards.add_card([opacity_row, frame_row, tint_row, corners_row, fades_row])
