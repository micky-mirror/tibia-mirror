"""A popup that asks for a name."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.config import MAX_NAME_LENGTH
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.popup import PAD, Popup
from tibia_mirror.ui.panel.controls.widgets import TextField


class NameDialog(Popup):
    """Asks for a name, starting with a suggested one."""

    def __init__(
        self,
        window: tk.Misc,
        title: str,
        suggested_name: str,
        on_ok: Callable[[str], None],
        on_cancel: Callable[[], None],
    ) -> None:
        super().__init__(window, title)
        self._suggested_name = suggested_name  # also the answer when the field is left empty
        self._on_ok = on_ok  # gets the name
        self._on_cancel = on_cancel
        self._name_text = tk.StringVar(value=suggested_name)

        self._name_field = self._add_name_field()
        self._add_buttons()
        self._open()
        self._select_name()

    def _add_name_field(self) -> TextField:
        name_field = TextField(
            self,
            self._name_text,
            width=self._content_width,
            background=theme.BG,
        )
        name_field.pack(anchor="w", padx=px(PAD))
        # Tk asks before every change. %P: the text the field would have after it.
        allowed_name = (self.register(self._is_allowed_name), "%P")
        name_field.entry.configure(validate="key", validatecommand=allowed_name)
        return name_field

    def _select_name(self) -> None:
        """Put the keys in the field with the whole name selected, so typing replaces it."""
        entry = self._name_field.entry
        entry.focus_set()
        entry.select_range(0, "end")
        entry.icursor("end")

    def _is_allowed_name(self, name: str) -> bool:
        return len(name) <= MAX_NAME_LENGTH

    def _confirm(self) -> None:
        name = self._name_text.get().strip() or self._suggested_name
        self.destroy()
        self._on_ok(name)

    def _cancel(self) -> None:
        self.destroy()
        self._on_cancel()
