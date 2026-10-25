"""A row of a card with a few options to choose from, such as the language."""

import tkinter as tk
from collections.abc import Callable, Sequence

from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.widgets import SegmentedDrawing
from tibia_mirror.ui.panel.rows.row import ROW_PAD, SIDE_PAD, draw_label


class ChoiceRow:
    """One setting with a few options to choose from."""

    def __init__(
        self,
        label: str,
        options: Sequence[tuple[str, str]],
        selected: str,
        on_change: Callable[[str], None],
    ) -> None:
        self._label = label
        self._options = options  # (key, text) of each option, from left to right
        self._selected = selected  # the key of the chosen option
        self._on_change = on_change  # called with the key of the option the user chose
        self._hovered: str | None = None  # the key of the option under the pointer
        self._pressed: str | None = None  # the key of the option the button went down on

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""
        label_end_y = draw_label(canvas, row_start_y, self._label)
        row_end_y = label_end_y + px(ROW_PAD)
        self._draw_options(canvas, row_start_y, row_end_y, width)
        return row_end_y

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Show the option under the pointer as hovered.

        Return True when a click at this place would choose an option.
        """
        option = self._get_option_at(position_x, position_y)
        self._set_hovered(option)
        return option is not None

    def pointer_left(self) -> None:
        """The pointer went out of the card: no option is hovered."""
        self._set_hovered(None)

    def set_selected(self, option: str) -> None:
        """Make `option` the chosen one and draw the options again."""
        self._selected = option
        self._hovered = None  # the chosen option has no hover look
        self._options_drawing.draw(self._selected, self._hovered)

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Remember the option the mouse button went down on."""
        self._pressed = self._get_option_at(position_x, position_y)

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Choose the option if the button went down and up on it, like a normal button."""
        option = self._get_option_at(position_x, position_y)
        if option is not None and option == self._pressed:
            self._select(option)
        self._pressed = None

    def _set_hovered(self, option: str | None) -> None:
        """Remember the hovered option and draw the options again, only when it changed."""
        if option == self._hovered:
            return
        self._hovered = option
        self._options_drawing.draw(self._selected, self._hovered)

    def _get_option_at(self, position_x: int, position_y: int) -> str | None:
        """The key of the option at this place, or None. The chosen option does not count."""
        option = self._options_drawing.at(position_x, position_y)
        if option == self._selected:
            return None
        return option

    def _select(self, option: str) -> None:
        """Make `option` the chosen one and report the choice."""
        self.set_selected(option)
        self._on_change(option)

    def _draw_options(
        self, canvas: tk.Canvas, row_start_y: int, row_end_y: int, width: int
    ) -> None:
        """The options side by side, at the right, in the middle of the row's height."""
        position_x = width - px(SIDE_PAD)  # the right end of the options
        position_y = (row_start_y + row_end_y) // 2  # the middle of the options
        # The drawing holds its images, so the row stores it.
        self._options_drawing = SegmentedDrawing(canvas, position_x, position_y, self._options)
        self._options_drawing.draw(self._selected, None)
