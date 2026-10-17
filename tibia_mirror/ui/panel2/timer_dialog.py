"""The settings of a mirror's timer."""

import tkinter as tk

from tibia_mirror.i18n import tr
from tibia_mirror.ui.panel2.popup import Popup


class TimerDialog(Popup):
    """Asks how the timer of one mirror works."""

    def __init__(self, window: tk.Misc, name: str) -> None:
        super().__init__(window, tr('Timer for "{name}"', name=name))

        self._open()
