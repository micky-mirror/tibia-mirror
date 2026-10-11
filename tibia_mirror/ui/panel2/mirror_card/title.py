"""The left part of the top row of a mirror card: the colour dot, the name and the size."""

import tkinter as tk
import tkinter.font as tkfont

from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import elide
from tibia_mirror.ui.panel2.mirror_card.colour_dot import ColourDot
from tibia_mirror.ui.panel2.mirror_card.layout import BUTTONS_ROOM, TOP_ROW_Y
from tibia_mirror.ui.panel2.mirror_card.text_link import TextLink
from tibia_mirror.ui.panel2.mirror_card.tip import Tip
from tibia_mirror.ui.panel2.mirror_info import MirrorInfo

# Sizes at 100% display scaling; px() scales them where they are used.
DOT_X = 18  # from the left side of the card to the middle of the colour dot
NAME_X = 33  # from the left side of the card to the start of the name
TEXT_GAP = 8  # between the name and the size, and between the size and the buttons


class MirrorCardTitle:
    """The left part of the top row of a mirror card.

    It has the dot in the colour of the mirror's frame, the name of the mirror,
    and the size of the mirrored area as a link.
    """

    def __init__(self, canvas: tk.Canvas, width: int, mirror: MirrorInfo) -> None:
        self._canvas = canvas
        self._width = width  # of the card
        self._mirror = mirror

        self._draw_colour_dot()
        self._draw_name()
        self._draw_size()

    def pointer_moved(self, position_x: int, position_y: int) -> bool:
        """Show the hover look of the dot or of the size link when the pointer is on it.

        Return True if it is on one of them.
        """
        is_over_dot: bool = self._colour_dot.contains(position_x, position_y)
        is_over_link: bool = self._size_link.contains(position_x, position_y)

        self._colour_dot.set_hovered(is_over_dot)
        self._size_link.set_hovered(is_over_link)
        return is_over_dot or is_over_link

    def pointer_left(self) -> None:
        """The pointer went out of the card: the dot and the size link have no hover look."""
        self._colour_dot.set_hovered(False)
        self._size_link.set_hovered(False)

    def pointer_pressed(self, position_x: int, position_y: int) -> None:
        """Remember if the mouse button went down on the dot or on the size link."""

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Open the choice of colours, or the settings of the area.

        Only if the mouse button went down and up on the dot, or on the size link.
        """

    def _draw_colour_dot(self) -> None:
        """The round dot before the name, in the colour of the mirror's frame.

        A click on it opens the choice of colours.
        """
        colour = theme.frame_color(self._mirror.colour)
        tip = Tip(tr("Frame colour"))

        self._colour_dot = ColourDot(self._canvas, px(DOT_X), px(TOP_ROW_Y), colour, tip)

    def _draw_name(self) -> None:
        """The name of the mirror in bold, cut short with "…" when it is too long.

        The name of a hidden mirror is grey.
        """
        font = tkfont.Font(font=theme.FONT_BOLD)
        # the name can take the width that the size and the buttons leave
        room = self._width - px(NAME_X) - self._get_size_width() - px(TEXT_GAP) - px(BUTTONS_ROOM)
        name = elide(self._mirror.name, font, room)
        self._canvas.create_text(
            px(NAME_X),
            px(TOP_ROW_Y),
            text=name,
            anchor="w",
            font=font,
            fill=theme.SUBTEXT if self._mirror.is_hidden else theme.TEXT,
        )
        # remembered because the size starts right after the name
        self._name_end_x = px(NAME_X) + font.measure(name)

    def _draw_size(self) -> None:
        """The size of the mirrored area, such as "320×64", in grey after the name.

        It works like a link: a click on it opens the settings of the area.
        """
        position_x = self._name_end_x + px(TEXT_GAP)
        text = self._get_size_text()
        tip = Tip(tr("Edit region"), tr("Position, size and zoom."))

        self._size_link = TextLink(self._canvas, position_x, px(TOP_ROW_Y), text, tip)

    def _get_size_text(self) -> str:
        return f"{self._mirror.area_width}×{self._mirror.area_height}"

    def _get_size_width(self) -> int:
        """The width of the size text on the screen, in pixels."""
        return tkfont.Font(font=theme.FONT).measure(self._get_size_text())
