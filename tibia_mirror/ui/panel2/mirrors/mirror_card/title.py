"""The left part of the top row of a mirror card: the colour dot, the name and the size."""

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable
from dataclasses import replace

from tibia_mirror.config import FRAME_COLORS, FRAME_COLORS_PER_ROW
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import elide
from tibia_mirror.ui.controls.menu import SwatchPicker
from tibia_mirror.ui.panel2.mirrors.mirror_card.colour_dot import ColourDot
from tibia_mirror.ui.panel2.mirrors.mirror_card.layout import BUTTONS_ROOM, TOP_ROW_Y
from tibia_mirror.ui.panel2.mirrors.mirror_card.text_link import TextLink
from tibia_mirror.ui.panel2.mirrors.mirror_card.tip import Tip
from tibia_mirror.ui.panel2.mirrors.mirror_info import MirrorInfo

# Sizes at 100% display scaling; px() scales them where they are used.
DOT_X = 18  # from the left side of the card to the middle of the colour dot
NAME_X = 33  # from the left side of the card to the start of the name
TEXT_GAP = 8  # between the name and the size, and between the size and the buttons


class MirrorCardTitle:
    """The left part of the top row of a mirror card.

    It has the dot in the colour of the mirror's frame, the name of the mirror,
    and the size of the mirrored area as a link.
    """

    def __init__(
        self,
        canvas: tk.Canvas,
        width: int,
        mirror: MirrorInfo,
        on_changed: Callable[[MirrorInfo], None],
        on_select_area: Callable[[str], None],
    ) -> None:
        self._canvas = canvas
        self._width = width  # of the card
        self._mirror = mirror
        self._on_changed = on_changed  # gets the new info after the colour was changed
        self._on_select_area = on_select_area  # gets the mirror id after the size was clicked
        # the dot or the link that the mouse button went down on
        self._pressed_piece: ColourDot | TextLink | None = None

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
        self._pressed_piece = self._get_piece_at(position_x, position_y)

    def pointer_released(self, position_x: int, position_y: int) -> None:
        """Open the choice of colours, or let the user select the area again.

        Only if the mouse button went down and up on the dot, or on the size link.
        """
        piece = self._get_piece_at(position_x, position_y)
        pressed_piece = self._pressed_piece
        self._pressed_piece = None

        if piece is not None and piece is pressed_piece:
            piece.click()

    def set_mirror(self, mirror: MirrorInfo) -> None:
        """Show the dot and the name for the new state of the mirror."""
        self._mirror = mirror
        self._colour_dot.set_colour(theme.frame_color(mirror.colour))
        self._canvas.itemconfigure(self._name_item, fill=self._get_name_colour())

    def _draw_colour_dot(self) -> None:
        """The round dot before the name, in the colour of the mirror's frame.

        A click on it opens the choice of colours.
        """
        colour = theme.frame_color(self._mirror.colour)
        tip = Tip(tr("Frame colour"))

        self._colour_dot = ColourDot(
            self._canvas,
            px(DOT_X),
            px(TOP_ROW_Y),
            colour,
            tip,
            self._pick_colour,
        )

    def _draw_name(self) -> None:
        """The name of the mirror in bold, cut short with "…" when it is too long.

        The name of a hidden mirror is grey.
        """
        font = tkfont.Font(font=theme.FONT_BOLD)
        # the name can take the width that the size and the buttons leave
        room = self._width - px(NAME_X) - self._get_size_width() - px(TEXT_GAP) - px(BUTTONS_ROOM)
        name = elide(self._mirror.name, font, room)
        self._name_item = self._canvas.create_text(
            px(NAME_X),
            px(TOP_ROW_Y),
            text=name,
            anchor="w",
            font=font,
            fill=self._get_name_colour(),
        )
        # remembered because the size starts right after the name
        self._name_end_x = px(NAME_X) + font.measure(name)

    def _get_name_colour(self) -> str:
        """Grey for a hidden mirror, the normal text colour if not."""
        return theme.SUBTEXT if self._mirror.is_hidden else theme.TEXT

    def _draw_size(self) -> None:
        """The size of the mirrored area, such as "320×64", in grey after the name.

        It works like a link: a click on it lets the user select the area again.
        """
        position_x = self._name_end_x + px(TEXT_GAP)
        text = self._get_size_text()
        tip = Tip(tr("Select area again"))

        self._size_link = TextLink(
            self._canvas,
            position_x,
            px(TOP_ROW_Y),
            text,
            tip,
            self._select_area_again,
        )

    def _get_size_text(self) -> str:
        return f"{self._mirror.area_width}×{self._mirror.area_height}"

    def _get_size_width(self) -> int:
        """The width of the size text on the screen, in pixels."""
        return tkfont.Font(font=theme.FONT).measure(self._get_size_text())

    def _get_piece_at(self, position_x: int, position_y: int) -> ColourDot | TextLink | None:
        """The dot or the size link at this place, or None."""
        if self._colour_dot.contains(position_x, position_y):
            return self._colour_dot
        if self._size_link.contains(position_x, position_y):
            return self._size_link

        return None

    def _pick_colour(self) -> None:
        """Open the choice of colours for the mirror's frame."""
        SwatchPicker(
            self._canvas.winfo_toplevel(),
            self._colour_dot.get_screen_box(),
            [(name, theme.frame_color(name)) for name in FRAME_COLORS],
            self._mirror.colour,
            on_pick=self._on_colour_picked,
            on_close=lambda: None,
            per_row=FRAME_COLORS_PER_ROW,
        )

    def _on_colour_picked(self, colour: str) -> None:
        """Hand up the mirror with its new frame colour. Do nothing when it is the same colour."""
        if colour == self._mirror.colour:
            return

        self._on_changed(replace(self._mirror, colour=colour))

    def _select_area_again(self) -> None:
        self._on_select_area(self._mirror.mirror_id)
