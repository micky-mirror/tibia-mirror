"""The settings of a mirror's timer."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.core.mirror_timer import MirrorTimer
from tibia_mirror.i18n import tr
from tibia_mirror.ui.panel2.popup import Popup


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
        self._timer = timer
        self._on_ok = on_ok

        self._add_buttons()
        self._open()

    def _confirm(self) -> None:
        """Close, and hand the timer to the card."""
        self.destroy()
        self._on_ok(self._timer)
