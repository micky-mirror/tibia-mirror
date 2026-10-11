"""A row of a settings card with a few options to choose from, such as the language."""

import tkinter as tk

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px

# Sizes at 100% display scaling; px() scales them where they are used.
SIDE_PAD = 14  # left and right of the row's content
ROW_PAD = 10  # above and below the row's content


class ChoiceRow:
    """One setting with a few options to choose from."""

    def __init__(self, label: str) -> None:
        self._label = label

    def draw(self, canvas: tk.Canvas, top: int) -> int:
        """Draw the row on the card, starting at `top`. Return where the row ends."""
        # draw label
        label = canvas.create_text(
            px(SIDE_PAD),
            top + px(ROW_PAD),
            text=self._label,
            anchor="nw",
            font=theme.FONT,
            fill=theme.TEXT,
        )

        # the row ends a little under the label
        label_bottom: int = canvas.bbox(label)[3]
        return label_bottom + px(ROW_PAD)
