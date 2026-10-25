"""A row of a card where the user sets a key, such as the key that hides all mirrors."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.core.timers import KeyCombo
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.dialogs import key_combo_name
from tibia_mirror.ui.panel.controls.widgets import KeyField
from tibia_mirror.ui.panel.rows.row import ROW_PAD, SIDE_PAD, draw_hint, draw_label
from tibia_mirror.winapi import win32

# Sizes at 100% display scaling; px() scales them where they are used.
FIELD_GAP = 8  # between the help text and the field for the key


class KeyRow:
    """One setting that is a key or a few keys together, such as Ctrl+H.

    The field for the key is a widget of its own. It hears the mouse and the
    keyboard by itself, so the pointer methods of the row have nothing to do.
    """

    def __init__(
        self,
        label: str,
        hint: str,
        key: KeyCombo | None,
        on_change: Callable[[KeyCombo | None], None],
    ) -> None:
        self._label = label
        self._hint = hint  # the help text under the label
        self._key = key  # the key that is set now, or None when no key is set
        self._on_change = on_change  # called with the new key, or None when it is cleared

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        content_width = width - 2 * px(SIDE_PAD)
        hint_end_y = draw_hint(canvas, label_end_y, self._hint, content_width)
        field_end_y = self._add_field(canvas, hint_end_y, content_width)
        return field_end_y + px(ROW_PAD)

    def set_key(self, key: KeyCombo | None) -> None:
        """Show another key in the field, after it was changed somewhere else."""
        self._key = key
        self._field.set_value(key)

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Nothing to do: the field for the key hears the pointer by itself."""
        return False

    def pointer_left(self) -> None:
        """Nothing to do: the field for the key hears the pointer by itself."""

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Nothing to do: the field for the key hears the pointer by itself."""

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Nothing to do: the field for the key hears the pointer by itself."""

    def _add_field(self, canvas: tk.Canvas, hint_end_y: int, width: int) -> int:
        """The field for the key, under the help text. Return the y where the field ends."""
        self._field = KeyField(
            canvas,
            self._key,
            width=width,
            background=theme.SURFACE,
            name=key_combo_name,
            empty=tr("Click to set a key"),
            waiting=tr("Press a key..."),
            modifiers=win32.modifiers_down,
            on_change=self._on_change,
        )
        field_start_y = hint_end_y + px(FIELD_GAP)
        canvas.create_window(px(SIDE_PAD), field_start_y, window=self._field, anchor="nw")
        return field_start_y + px(KeyField.HEIGHT)
