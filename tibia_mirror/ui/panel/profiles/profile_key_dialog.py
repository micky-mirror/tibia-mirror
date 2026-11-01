"""The key that opens a profile."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.core.keys import KeyCombo
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.popup import PAD, Popup
from tibia_mirror.ui.panel.rows.key_row import KeyRow
from tibia_mirror.ui.panel.rows.row_card import RowCard


class ProfileKeyDialog(Popup):
    """Asks for the key that opens the profile `name`."""

    def __init__(
        self,
        window: tk.Misc,
        name: str,
        key: KeyCombo | None,
        on_ok: Callable[[KeyCombo | None], None],
    ) -> None:
        super().__init__(window, tr('Key for "{name}"', name=name))
        self._key = key  # with the change made in the dialog; None when it has no key
        self._on_ok = on_ok  # gets the key, or None when it was cleared

        self._add_key_card()
        self._add_buttons(tr("OK"))
        self._open()

    def _add_key_card(self) -> None:
        """The key, on a card like the one of the Timer dialog."""
        key_row = KeyRow(
            tr("Key"),
            tr("Assign profile to the key."),
            key=self._key,
            on_change=self._keep_key,
        )
        card = RowCard(self, self._content_width, [key_row])
        card.pack(anchor="w", padx=px(PAD))

    def _keep_key(self, key: KeyCombo | None) -> None:
        """Keep the key set in the row, until OK."""
        self._key = key

    def _confirm(self) -> None:
        self.destroy()
        self._on_ok(self._key)
