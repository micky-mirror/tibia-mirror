"""What every row of a settings card has in common."""

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

    def draw(self, canvas: tk.Canvas, top: int, width: int) -> int:
        """Draw the row on the card, starting at `top`. Return where the row ends."""

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Show the hover look. Return True when a click at this place would do something."""

    def pointer_left(self) -> None:
        """The pointer went out of the card."""

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """The mouse button went down at this place."""

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """The mouse button went up at this place."""


def draw_label(canvas: tk.Canvas, top: int, text: str) -> int:
    """Draw the name of a setting at the left of its row. Return where the text ends."""
    label = canvas.create_text(
        px(SIDE_PAD),
        top + px(ROW_PAD),
        text=text,
        anchor="nw",
        font=theme.FONT,
        fill=theme.TEXT,
    )
    label_bottom: int = canvas.bbox(label)[3]
    return label_bottom


def draw_hint(canvas: tk.Canvas, top: int, text: str, width: int) -> int:
    """Draw the help text of a setting under its label, which ends at `top`.

    Long text breaks into lines at `width`. Return where the text ends.
    """
    hint = canvas.create_text(
        px(SIDE_PAD),
        top + px(HINT_GAP),
        text=text,
        anchor="nw",
        width=width,
        font=theme.FONT_SMALL,
        fill=theme.SUBTEXT,
    )
    hint_bottom: int = canvas.bbox(hint)[3]
    return hint_bottom
