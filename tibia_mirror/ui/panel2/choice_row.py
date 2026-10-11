"""A row of a settings card with a few options to choose from, such as the language."""

import tkinter as tk
from collections.abc import Sequence

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.controls.widgets import SegmentedDrawing
from tibia_mirror.ui.panel2.row import ROW_PAD, SIDE_PAD


class ChoiceRow:
    """One setting with a few options to choose from."""

    def __init__(self, label: str, options: Sequence[tuple[str, str]], selected: str) -> None:
        self._label = label
        self._options = options  # (key, text) of each option, from left to right
        self._selected = selected  # the key of the chosen option
        self._hovered: str | None = None  # the key of the option under the pointer
        self._pressed: str | None = None  # the key of the option the button went down on

    def draw(self, canvas: tk.Canvas, top: int, width: int) -> int:
        """Draw the row on the card, starting at `top`. Return where the row ends."""
        label_bottom = self._draw_label(canvas, top)
        bottom = label_bottom + px(ROW_PAD)
        self._draw_options(canvas, top, bottom, width)
        return bottom

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Show the option under the pointer as hovered.

        Return True when a click at this place would choose an option.
        """
        option = self._option_at(position_x, position_y)
        self._set_hovered(option)
        return option is not None

    def pointer_left(self) -> None:
        """The pointer went out of the card: no option is hovered."""
        self._set_hovered(None)

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Remember the option the mouse button went down on."""
        self._pressed = self._option_at(position_x, position_y)

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Choose the option if the button went down and up on it, like a normal button."""
        option = self._option_at(position_x, position_y)
        if option is not None and option == self._pressed:
            self._select(option)
        self._pressed = None

    def _set_hovered(self, option: str | None) -> None:
        """Remember the hovered option and draw the options again, only when it changed."""
        if option == self._hovered:
            return
        self._hovered = option
        self._options_drawing.draw(self._selected, self._hovered)

    def _option_at(self, position_x: int, position_y: int) -> str | None:
        """The key of the option at this place, or None. The chosen option does not count."""
        option = self._options_drawing.at(position_x, position_y)
        if option == self._selected:
            return None
        return option

    def _select(self, option: str) -> None:
        """Make `option` the chosen one and draw the options again."""
        self._selected = option
        self._hovered = None  # the chosen option has no hover look
        self._options_drawing.draw(self._selected, self._hovered)

    def _draw_label(self, canvas: tk.Canvas, top: int) -> int:
        """The name of the setting, at the left. Return where the text ends."""
        label = canvas.create_text(
            px(SIDE_PAD),
            top + px(ROW_PAD),
            text=self._label,
            anchor="nw",
            font=theme.FONT,
            fill=theme.TEXT,
        )
        label_bottom: int = canvas.bbox(label)[3]
        return label_bottom

    def _draw_options(self, canvas: tk.Canvas, top: int, bottom: int, width: int) -> None:
        """The options side by side, at the right, in the middle of the row's height."""
        position_x = width - px(SIDE_PAD)  # the right end of the options
        position_y = (top + bottom) // 2  # the middle of the options
        # The drawing holds its images, so the row stores it.
        self._options_drawing = SegmentedDrawing(canvas, position_x, position_y, self._options)
        self._options_drawing.draw(self._selected, None)
