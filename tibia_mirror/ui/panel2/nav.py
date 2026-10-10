"""The menu on the left side of the panel."""

import tkinter as tk

from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px


class NavRail(tk.Canvas):
    """The menu on the left. For now it draws one entry: Mirrors."""

    # Sizes at 100% display scaling; px() scales them where they are used.
    WIDTH = 100
    TOP_PAD = 16  # above the entry
    ICON_HEIGHT = 30
    LABEL_GAP = 4  # between the icon and the label

    def __init__(self, parent: tk.Misc) -> None:
        # No focus ring and no border: Tk adds both to a canvas.
        super().__init__(parent, width=px(self.WIDTH), bg=theme.MANTLE, highlightthickness=0, bd=0)
        self._draw_mirror_nav()

    def _draw_mirror_nav(self) -> None:
        # start icon positions
        position_x = px(self.WIDTH) // 2
        position_y = px(self.TOP_PAD) + px(self.ICON_HEIGHT) // 2
        # label position from top
        label_y = position_y + px(self.ICON_HEIGHT) // 2 + px(self.LABEL_GAP)
        # draw icon
        self.create_text(
            position_x,
            position_y,
            text="\ue8b9",
            font=theme.FONT_ICON_LARGE,
            fill=theme.SUBTEXT,
        )
        # draw text
        self.create_text(
            position_x,
            label_y,
            text=tr("Mirrors"),
            anchor="n",
            font=theme.FONT_CAPTION,
            fill=theme.SUBTEXT,
        )
