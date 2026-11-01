"""A row of a card where the user writes a time in minutes and seconds, such as the alert time."""

import tkinter as tk

from tibia_mirror.core.mirrors.timers import parse_alert
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.rows.row import SIDE_PAD
from tibia_mirror.ui.panel.rows.two_field_row import TwoFieldRow

# Sizes at 100% display scaling; px() scales them where they are used.
SECONDS_GAP = 16  # between the unit of the minutes and the field of the seconds


class TimeRow(TwoFieldRow):
    """One setting that is a time in minutes and seconds, such as 1:30."""

    FIELD_WIDTH = 52  # room for two digits
    MAX_DIGITS = 2  # the minutes and the seconds go up to 59

    def __init__(self, label: str, hint: str, seconds: int) -> None:
        super().__init__(label, hint)
        self._seconds = seconds  # the time that the fields show first

    def get_seconds(self) -> int | None:
        """The time written in the fields, in seconds. None if it is not from 0:01 to 59:59."""
        minutes_field, seconds_field = self._fields

        return parse_alert(minutes_field.get_text(), seconds_field.get_text())

    def set_error(self, is_error: bool) -> None:
        """Show the fields with a red border, or with the normal one again."""
        for field in self._fields:
            field.set_error(is_error)

    def _add_fields(self, canvas: tk.Canvas, fields_start_y: int) -> None:
        """The minutes and the seconds side by side, each with its unit after it."""
        minutes, seconds = divmod(self._seconds, 60)

        minutes_end_x = self._add_field(
            canvas, px(SIDE_PAD), fields_start_y, str(minutes), tr("min")
        )
        seconds_start_x = minutes_end_x + px(SECONDS_GAP)
        self._add_field(canvas, seconds_start_x, fields_start_y, f"{seconds:02d}", tr("s"))

    def _on_text_changed(self, text: str) -> None:
        self.set_error(False)
