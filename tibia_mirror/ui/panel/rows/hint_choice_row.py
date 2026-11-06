"""A row of a card with a few options to choose from, and a help text under them."""

import tkinter as tk
from collections.abc import Callable, Sequence

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.rows.row import ROW_PAD, SIDE_PAD, draw_hint
from tibia_mirror.ui.panel.rows.segmented_row import SegmentedRow


class HintChoiceRow(SegmentedRow):
    """One setting with a few options to choose from, explained by a help text."""

    def __init__(
        self,
        label: str,
        hint: str,
        *,
        options: Sequence[tuple[str, str]],
        selected: str,
        on_change: Callable[[str], None],
        font: theme.FontSpec = theme.FONT,
    ) -> None:
        super().__init__(label, options, selected, on_change, font=font)
        self._hint = hint  # the help text under the label

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        line_end_y = self._draw_label_and_options(canvas, row_start_y, width)
        content_width = width - 2 * px(SIDE_PAD)
        hint_end_y = draw_hint(canvas, line_end_y, self._hint, content_width)
        return hint_end_y + px(ROW_PAD)
