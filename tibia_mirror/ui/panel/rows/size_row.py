"""A row of a card where the user writes a size in pixels: a width and a height."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.config import MIN_SELECTION_SIDE
from tibia_mirror.settings.app_settings import BoxSize
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.rows.row import SIDE_PAD
from tibia_mirror.ui.panel.rows.two_field_row import UNIT_GAP, TwoFieldRow


class SizeRow(TwoFieldRow):
    """One setting that is a width and a height in pixels."""

    FIELD_WIDTH = 64  # room for four digits
    MAX_DIGITS = 4

    def __init__(
        self,
        label: str,
        hint: str,
        *,
        size: BoxSize,
        on_change: Callable[[BoxSize], None],
    ) -> None:
        super().__init__(label, hint)
        self._size = size  # the size that the fields show first
        self._on_change = on_change  # called with each new size that is big enough

    def _add_fields(self, canvas: tk.Canvas, fields_start_y: int) -> None:
        """The width and the height side by side, as in "32 x 32 px"."""
        width, height = self._size

        width_end_x = self._add_field(canvas, px(SIDE_PAD), fields_start_y, str(width), "x")
        height_start_x = width_end_x + px(UNIT_GAP)
        self._add_field(canvas, height_start_x, fields_start_y, str(height), "px")

    def _get_size(self) -> BoxSize | None:
        """The size written in the fields. None if a side is empty or too small."""
        width_field, height_field = self._fields
        width_text = width_field.get_text()
        height_text = height_field.get_text()

        if width_text == "" or height_text == "":
            return None

        width, height = int(width_text), int(height_text)

        if width < MIN_SELECTION_SIDE or height < MIN_SELECTION_SIDE:
            return None

        return width, height

    def _on_text_changed(self, text: str) -> None:
        size = self._get_size()
        is_error = size is None

        for field in self._fields:
            field.set_error(is_error)

        if size is not None:
            self._on_change(size)
