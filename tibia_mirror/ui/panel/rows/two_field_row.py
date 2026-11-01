"""The base of the rows of a card with two number fields, each with a unit after it."""

import string
import tkinter as tk
from abc import ABC, abstractmethod
from typing import ClassVar

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.text_field import HEIGHT as FIELD_HEIGHT
from tibia_mirror.ui.panel.controls.text_field import TextField
from tibia_mirror.ui.panel.rows.row import ROW_PAD, SIDE_PAD, draw_hint, draw_label

# Sizes at 100% display scaling; px() scales them where they are used.
FIELDS_TOP_PAD = 8  # between the help text and the fields
UNIT_GAP = 6  # between a field and its unit


class TwoFieldRow(ABC):
    """The base of every row with two number fields.

    The fields are widgets of their own. They hear the mouse and the keyboard by
    themselves, so the pointer methods of the row have nothing to do.
    """

    FIELD_WIDTH: ClassVar[int]  # at 100% display scaling, with room for MAX_DIGITS
    MAX_DIGITS: ClassVar[int]  # the most digits a field takes

    def __init__(self, label: str, hint: str) -> None:
        self._label = label
        self._hint = hint  # the help text under the label
        self._fields: list[TextField] = []  # the first field, then the second

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        content_width = width - 2 * px(SIDE_PAD)
        hint_end_y = draw_hint(canvas, label_end_y, self._hint, content_width)
        fields_start_y = hint_end_y + px(FIELDS_TOP_PAD)
        self._add_fields(canvas, fields_start_y)
        return fields_start_y + px(FIELD_HEIGHT) + px(ROW_PAD)

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Nothing to do: the fields hear the pointer by themselves."""
        return False

    def pointer_left(self) -> None:  # noqa: B027
        """Nothing to do: the fields hear the pointer by themselves."""

    def pointer_pressed(self, position_x: int, position_y: int) -> None:  # noqa: B027
        """Nothing to do: the fields hear the pointer by themselves."""

    def pointer_released(self, position_x: int, position_y: int) -> None:  # noqa: B027
        """Nothing to do: the fields hear the pointer by themselves."""

    @abstractmethod
    def _add_fields(self, canvas: tk.Canvas, fields_start_y: int) -> None:
        """Both fields side by side, each one added with `_add_field`."""

    @abstractmethod
    def _on_text_changed(self, text: str) -> None:
        """What the row does after each change in one of its fields."""

    def _add_field(
        self,
        canvas: tk.Canvas,
        field_start_x: int,
        fields_start_y: int,
        text: str,
        unit: str,
    ) -> int:
        """One field with its unit after it. Return the x where the unit ends."""
        field = TextField(
            canvas,
            text,
            width=px(self.FIELD_WIDTH),
            background=theme.SURFACE,
            is_allowed=self._is_allowed_text,
            on_change=self._on_text_changed,
        )
        canvas.create_window(field_start_x, fields_start_y, window=field, anchor="nw")
        self._fields.append(field)
        unit_text = canvas.create_text(
            field_start_x + px(self.FIELD_WIDTH) + px(UNIT_GAP),
            fields_start_y + px(FIELD_HEIGHT) // 2,
            text=unit,
            anchor="w",
            font=theme.FONT,
            fill=theme.SUBTEXT,
        )
        unit_end_x: int = canvas.bbox(unit_text)[2]
        return unit_end_x

    def _is_allowed_text(self, text: str) -> bool:
        return len(text) <= self.MAX_DIGITS and all(char in string.digits for char in text)
