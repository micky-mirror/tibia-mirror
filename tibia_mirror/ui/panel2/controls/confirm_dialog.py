"""A popup that asks the user to accept or cancel."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel2.controls.popup import PAD, Popup


class ConfirmDialog(Popup):
    """Shows a short text with Cancel and OK."""

    def __init__(
        self,
        window: tk.Misc,
        title: str,
        text: str,
        on_ok: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        super().__init__(window, title)
        self._on_ok = on_ok
        self._on_cancel = on_cancel

        self._add_text(text)
        self._add_buttons()
        self._open()

    def _add_text(self, text: str) -> None:
        label = tk.Label(
            self,
            text=text,
            bg=theme.BG,
            fg=theme.SUBTEXT,
            font=theme.FONT,
            bd=0,
            padx=0,
            justify="left",
            wraplength=self._content_width,
        )
        label.pack(anchor="w", padx=px(PAD))

    def _confirm(self) -> None:
        self.destroy()
        self._on_ok()

    def _cancel(self) -> None:
        self.destroy()
        self._on_cancel()
