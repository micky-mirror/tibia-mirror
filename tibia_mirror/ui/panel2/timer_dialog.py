"""The settings of a mirror's timer."""

import tkinter as tk
from collections.abc import Callable
from dataclasses import replace

from tibia_mirror.core.mirror_timer import MirrorTimer
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.choice_row import ChoiceRow
from tibia_mirror.ui.panel2.key_row import KeyRow
from tibia_mirror.ui.panel2.popup import PAD, Popup
from tibia_mirror.ui.panel2.row_card import RowCard
from tibia_mirror.ui.panel2.toggle_row import ToggleRow


class TimerDialog(Popup):
    """Asks how the timer of one mirror works."""

    def __init__(
        self,
        window: tk.Misc,
        name: str,
        timer: MirrorTimer,
        on_ok: Callable[[MirrorTimer], None],
    ) -> None:
        super().__init__(window, tr('Timer for "{name}"', name=name))
        self._timer = timer  # with the changes made in the dialog
        self._on_ok = on_ok

        self._add_timer_card()
        self._add_buttons()
        self._open()

    def _add_timer_card(self) -> None:
        """The rows of the timer, on a card like the ones of the Settings page."""
        timer_on_row = ToggleRow(
            tr("Timer on"),
            tr("Counts time since you click this region or press its key."),
            is_on=self._timer.is_on,
            on_change=lambda is_on: self._keep_timer(replace(self._timer, is_on=is_on)),
        )
        direction_row = ChoiceRow(
            tr("Count"),
            (("down", tr("Down")), ("up", tr("Up"))),
            self._timer.direction,
            on_change=lambda direction: self._keep_timer(replace(self._timer, direction=direction)),
        )
        key_row = KeyRow(
            tr("Key"),
            tr("A click on this region in the game, or the key, starts it again."),
            key=self._timer.key,
            on_change=lambda key: self._keep_timer(replace(self._timer, key=key)),
        )
        pause_row = ToggleRow(
            tr("Pause while logged out"),
            tr(
                "For timers that only count while your character is online: "
                "each character continues from where it logged out."
            ),
            is_on=self._timer.is_paused_offline,
            on_change=lambda is_on: self._keep_timer(replace(self._timer, is_paused_offline=is_on)),
        )

        card = RowCard(self, self._content_width, [timer_on_row, direction_row, key_row, pause_row])
        card.pack(anchor="w", padx=px(PAD))

    def _keep_timer(self, timer: MirrorTimer) -> None:
        """Keep the timer with a change made in a row, until OK."""
        self._timer = timer

    def _confirm(self) -> None:
        """Close, and hand the timer with its changes to the card."""
        self.destroy()
        self._on_ok(self._timer)
