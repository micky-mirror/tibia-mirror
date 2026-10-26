"""A popup that asks for a name."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.config import MAX_NAME_LENGTH
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.popup import PAD, Popup
from tibia_mirror.ui.panel.controls.widgets import TextField

# Sizes at 100% display scaling; px() scales them where they are used.
ERROR_GAP = 6  # between the field and the error line


class NameDialog(Popup):
    """Asks for a name, starting with a suggested one.

    With `get_name_error`, a wrong name is not accepted: the reason shows under the field.
    """

    def __init__(
        self,
        window: tk.Misc,
        title: str,
        suggested_name: str,
        on_ok: Callable[[str], None],
        on_cancel: Callable[[], None],
        *,
        get_name_error: Callable[[str], str | None] | None = None,
    ) -> None:
        super().__init__(window, title)
        self._suggested_name = suggested_name  # also the answer when the field is left empty
        self._on_ok = on_ok  # gets the name
        self._on_cancel = on_cancel
        # gives why a name can't be used, in English, or None; without it every name is fine
        self._get_name_error = get_name_error
        self._name_text = tk.StringVar(value=suggested_name)

        self._name_field = self._add_name_field()
        self._error_line = self._add_error_line()
        self._add_buttons(tr("OK"))
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
        self._name_text.trace_add("write", self._on_name_changed)
        return name_field

    def _add_error_line(self) -> tk.Label:
        """The red reason under the field. Packed only while OK found the name wrong."""
        return tk.Label(
            self,
            bg=theme.BG,
            fg=theme.RED,
            font=theme.FONT_SMALL,
            bd=0,
            padx=0,
            justify="left",
            wraplength=self._content_width,
        )

    def _select_name(self) -> None:
        """Put the keys in the field with the whole name selected, so typing replaces it."""
        entry = self._name_field.entry
        entry.focus_set()
        entry.select_range(0, "end")
        entry.icursor("end")

    def _is_allowed_name(self, name: str) -> bool:
        return len(name) <= MAX_NAME_LENGTH

    def _on_name_changed(self, *trace_details: str) -> None:
        # the changed name may be fine, so the old reason goes away
        if self._error_line.winfo_manager():
            self._hide_error()

    def _show_error(self, error: str) -> None:
        """Show why the name can't be used, and make the field red."""
        self._error_line.configure(text=tr(error))
        self._error_line.pack(
            after=self._name_field, anchor="w", padx=px(PAD), pady=(px(ERROR_GAP), 0)
        )
        self._name_field.set_error(True)
        self._fit_height()

    def _hide_error(self) -> None:
        self._error_line.pack_forget()
        self._name_field.set_error(False)
        self._fit_height()

    def _confirm(self) -> None:
        name = self._name_text.get().strip() or self._suggested_name
        error = None if self._get_name_error is None else self._get_name_error(name)

        if error is not None:
            self._show_error(error)
            return

        self.destroy()
        self._on_ok(name)

    def _cancel(self) -> None:
        self.destroy()
        self._on_cancel()
