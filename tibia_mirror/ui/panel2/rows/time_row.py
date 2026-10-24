"""A row of a card where the user writes a time in minutes and seconds, such as the alert time."""

import string
import tkinter as tk

from tibia_mirror.core.timers import parse_alert
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.widgets import TextField
from tibia_mirror.ui.panel2.rows.row import ROW_PAD, SIDE_PAD, draw_hint, draw_label

# Sizes at 100% display scaling; px() scales them where they are used.
FIELDS_TOP_PAD = 8  # between the help text and the fields
FIELD_WIDTH = 52  # room for two digits
UNIT_GAP = 6  # between a field and its unit
SECONDS_GAP = 16  # between the unit of the minutes and the field of the seconds

MAX_DIGITS = 2  # the minutes and the seconds go up to 59


class TimeRow:
    """One setting that is a time in minutes and seconds, such as 1:30.

    The fields are widgets of their own. They hear the mouse and the keyboard by
    themselves, so the pointer methods of the row have nothing to do.
    """

    def __init__(self, label: str, hint: str, seconds: int) -> None:
        self._label = label
        self._hint = hint  # the help text under the label
        self._seconds = seconds  # the time that the fields show first
        self._fields: list[TextField] = []  # the field of the minutes, then of the seconds

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        content_width = width - 2 * px(SIDE_PAD)
        hint_end_y = draw_hint(canvas, label_end_y, self._hint, content_width)
        fields_start_y = hint_end_y + px(FIELDS_TOP_PAD)
        self._add_fields(canvas, fields_start_y)
        return fields_start_y + px(TextField.HEIGHT) + px(ROW_PAD)

    def get_seconds(self) -> int | None:
        """The time written in the fields, in seconds. None if it is not from 0:01 to 59:59."""
        return parse_alert(self._minutes_text.get(), self._seconds_text.get())

    def set_error(self, is_error: bool) -> None:
        """Show the fields with a red border, or with the normal one again."""
        for field in self._fields:
            field.set_error(is_error)

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Nothing to do: the fields hear the pointer by themselves."""
        return False

    def pointer_left(self) -> None:
        """Nothing to do: the fields hear the pointer by themselves."""

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Nothing to do: the fields hear the pointer by themselves."""

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Nothing to do: the fields hear the pointer by themselves."""

    def _add_fields(self, canvas: tk.Canvas, fields_start_y: int) -> None:
        """The minutes and the seconds side by side, each with its unit after it."""
        minutes, seconds = divmod(self._seconds, 60)
        # the row keeps the texts: Tk empties a field whose text is thrown away
        self._minutes_text = tk.StringVar(canvas, str(minutes))
        self._seconds_text = tk.StringVar(canvas, f"{seconds:02d}")

        minutes_end_x = self._add_field(
            canvas, px(SIDE_PAD), fields_start_y, self._minutes_text, tr("min")
        )
        seconds_start_x = minutes_end_x + px(SECONDS_GAP)
        self._add_field(canvas, seconds_start_x, fields_start_y, self._seconds_text, tr("s"))

    def _add_field(
        self,
        canvas: tk.Canvas,
        field_start_x: int,
        fields_start_y: int,
        text: tk.StringVar,
        unit: str,
    ) -> int:
        """One field with its unit after it. Return the x where the unit ends."""
        field = TextField(canvas, text, width=px(FIELD_WIDTH), background=theme.SURFACE)
        canvas.create_window(field_start_x, fields_start_y, window=field, anchor="nw")
        self._fields.append(field)
        text.trace_add("write", self._on_text_changed)
        # Tk asks before every change. %P: the text the field would have after it.
        allowed_text = (canvas.register(self._is_allowed_text), "%P")
        field.entry.configure(validate="key", validatecommand=allowed_text)
        unit_text = canvas.create_text(
            field_start_x + px(FIELD_WIDTH) + px(UNIT_GAP),
            fields_start_y + px(TextField.HEIGHT) // 2,
            text=unit,
            anchor="w",
            font=theme.FONT,
            fill=theme.SUBTEXT,
        )
        unit_end_x: int = canvas.bbox(unit_text)[2]
        return unit_end_x

    def _is_allowed_text(self, text: str) -> bool:
        return len(text) <= MAX_DIGITS and all(char in string.digits for char in text)

    def _on_text_changed(self, *trace_details: str) -> None:
        self.set_error(False)
