"""What every row of a settings card has in common.

How the rows are placed: a canvas places nothing for us, and a row does not know
its height before it is drawn, because the height depends on the font and on how
the help text breaks into lines. So everything is drawn from top to bottom, and
each drawing gives back the y where it ended. The next thing starts at that y:

    label_end_y = draw_label(canvas, row_start_y, label)
    hint_end_y = draw_hint(canvas, label_end_y, hint, width)
    row_end_y = hint_end_y + px(ROW_PAD)

The card does the same with whole rows: `row_end_y` of one row is `row_start_y`
of the next row, and the end of the last row is the height of the card.
"""

import tkinter as tk
from typing import Protocol

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px

# Sizes at 100% display scaling; px() scales them where they are used.
SIDE_PAD = 14  # left and right of a row's content
ROW_PAD = 10  # above and below a row's content
HINT_GAP = 2  # between a label and the help text under it


class Row(Protocol):
    """What a settings card needs from a row. Every kind of row has these methods."""

    def draw(self, canvas: tk.Canvas, row_start_y: int, width: int) -> int:
        """Draw the row on the card from `row_start_y` down. Return the y where the row ends."""

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Show the hover look. Return True when a click at this place would do something."""

    def pointer_left(self) -> None:
        """The pointer went out of the card."""

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """The mouse button went down at this place."""

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """The mouse button went up at this place."""


def draw_label(canvas: tk.Canvas, row_start_y: int, text: str) -> int:
    """Draw the name of a setting at the left of its row. Return the y where the text ends."""
    label = canvas.create_text(
        px(SIDE_PAD),
        row_start_y + px(ROW_PAD),
        text=text,
        anchor="nw",
        font=theme.FONT,
        fill=theme.TEXT,
    )
    label_end_y: int = canvas.bbox(label)[3]
    return label_end_y


def draw_hint(canvas: tk.Canvas, label_end_y: int, text: str, width: int) -> int:
    """Draw the help text of a setting under its label.

    Long text breaks into lines at `width`. Return the y where the text ends.
    """
    hint = canvas.create_text(
        px(SIDE_PAD),
        label_end_y + px(HINT_GAP),
        text=text,
        anchor="nw",
        width=width,
        font=theme.FONT_SMALL,
        fill=theme.SUBTEXT,
    )
    hint_end_y: int = canvas.bbox(hint)[3]
    return hint_end_y
