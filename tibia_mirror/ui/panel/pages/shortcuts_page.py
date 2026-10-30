"""The Shortcuts page: keys that act on the mirrors while Tibia is active."""

import tkinter as tk

from tibia_mirror.app_parts.profile_manager import ProfileManager
from tibia_mirror.core.keys import KeyCombo
from tibia_mirror.i18n import tr
from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.panel.rows.key_row import KeyRow
from tibia_mirror.ui.panel.rows.scroll_cards import ScrollCards


class ShortcutsPage(tk.Frame):
    """The Shortcuts page."""

    def __init__(
        self,
        parent: tk.Misc,
        width: int,
        side_pad: int,
        settings: AppSettingsStore,
        profile_manager: ProfileManager,
    ) -> None:
        super().__init__(parent, bg=theme.BG)
        self._width = width
        self._side_pad = side_pad
        self._settings = settings
        self._profile_manager = profile_manager
        # initialize scrollable card
        self._add_scroll_cards()
        # add card blocks to scrollable card
        self._add_mirrors_group()
        # show a hotkey that was changed somewhere else, for example taken by a timer
        self._settings.add_listener(self._on_settings_changed)

    def destroy(self) -> None:
        """Stop listening to the settings before the page goes away."""
        self._settings.remove_listener(self._on_settings_changed)
        super().destroy()

    def _add_scroll_cards(self) -> None:
        """The scrolling column that holds the groups of the page."""
        self._scroll_cards = ScrollCards(self, self._width, self._side_pad)
        self._scroll_cards.pack(side="top", fill="both", expand=True)

    def _add_mirrors_group(self) -> None:
        """The only group: keys that act on all mirrors at once."""
        self._scroll_cards.add_caption(tr("MIRRORS"))
        self._hide_all_row = KeyRow(
            tr("Hide all mirrors"),
            tr("Press again to bring them back. Works while Tibia is active."),
            key=self._settings.current.hide_all_key,
            on_change=self._set_hide_all_key,
        )
        self._scroll_cards.add_card([self._hide_all_row])

    def _set_hide_all_key(self, key: KeyCombo | None) -> None:
        """Keep the hide-all key. A key that is new here is first cleared everywhere else."""
        if key is not None and key != self._settings.current.hide_all_key:
            self._profile_manager.clear_hotkey(key)

        self._settings.update(hide_all_key=key)

    def _on_settings_changed(self) -> None:
        self._hide_all_row.set_key(self._settings.current.hide_all_key)
