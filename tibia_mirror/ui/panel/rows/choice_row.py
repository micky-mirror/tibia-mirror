"""A row of a card with a few options to choose from, such as the language."""

import tkinter as tk

from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.rows.row import ROW_PAD, draw_label
from tibia_mirror.ui.panel.rows.segmented_row import SegmentedRow


class ChoiceRow(SegmentedRow):
    """One setting with a few options to choose from."""

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        self._draw_options(canvas, row_start_y, label_end_y, width)
        return label_end_y + px(ROW_PAD)

    def set_selected(self, option: str) -> None:
        """Make `option` the chosen one, without reporting it."""
        self._segmented_control.set_selected(option)
