"""The card of one mirror on the Mirrors page."""

import tkinter as tk
import tkinter.font as tkfont

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import elide
from tibia_mirror.ui.panel2.icon_button import IconButton
from tibia_mirror.ui.panel2.mirror_info import MirrorInfo

REMOVE_ICON = "✕"

# Sizes at 100% display scaling; px() scales them where they are used.
HEIGHT = 62
RADIUS = 8  # of the rounded corners
TOP_ROW_Y = 20  # from the top of the card to the middle line of the name and the buttons
DOT_X = 18  # from the left side of the card to the middle of the colour dot
DOT_SIZE = 10
NAME_X = 33  # from the left side of the card to the start of the name
# four buttons of 26, three gaps of 2, 8 at the right of them and 8 at the left
BUTTONS_ROOM = 126  # kept free at the right side of the card, for the four buttons
BUTTONS_RIGHT_PAD = 8  # from the right side of the card to the last button
BUTTON_GAP = 2  # between two buttons
TEXT_GAP = 8  # between the name and the size, and between the size and the buttons


class MirrorCard(tk.Canvas):
    """The card of one mirror: its name and size, its buttons and its opacity slider."""

    def __init__(self, parent: tk.Misc, width: int, mirror: MirrorInfo) -> None:
        # No focus ring and no border: Tk adds both to a canvas.
        super().__init__(
            parent,
            width=width,
            height=px(HEIGHT),
            bg=theme.BG,
            highlightthickness=0,
            bd=0,
        )
        self._width = width
        self._mirror = mirror  # what the card shows
        self._draw_background()
        self._draw_colour_dot()
        self._draw_name()
        self._draw_size()
        self._draw_buttons()

    def _draw_background(self) -> None:
        """The rounded shape of the card, a little lighter than the page."""
        self._background = rounded_image(
            self,
            width=self._width,
            height=px(HEIGHT),
            radius=px(RADIUS),
            colour=theme.SURFACE,
            background=theme.BG,
        )
        self.create_image(0, 0, anchor="nw", image=self._background)

    def _draw_colour_dot(self) -> None:
        """The round dot before the name, in the colour of the mirror's frame.

        A click on it opens the choice of colours.
        """
        size = px(DOT_SIZE)
        self._dot_image = rounded_image(
            self,
            width=size,
            height=size,
            radius=size // 2,  # half of the size: a full circle
            colour=theme.frame_color(self._mirror.colour),
            background=theme.SURFACE,  # the colour of the card around the dot
        )
        self.create_image(px(DOT_X), px(TOP_ROW_Y), image=self._dot_image)

    def _draw_name(self) -> None:
        """The name of the mirror in bold, cut short with "…" when it is too long.

        The name of a hidden mirror is grey.
        """
        font = tkfont.Font(font=theme.FONT_BOLD)
        # the name can take the width that the size and the buttons leave
        room = self._width - px(NAME_X) - self._size_width() - px(TEXT_GAP) - px(BUTTONS_ROOM)
        name = elide(self._mirror.name, font, room)
        self.create_text(
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
        self.create_text(
            self._name_end_x + px(TEXT_GAP),
            px(TOP_ROW_Y),
            text=self._size_text(),
            anchor="w",
            font=theme.FONT,
            fill=theme.SUBTEXT,
        )

    def _size_text(self) -> str:
        return f"{self._mirror.area_width}×{self._mirror.area_height}"

    def _size_width(self) -> int:
        """The width of the size text on the screen, in pixels."""
        return tkfont.Font(font=theme.FONT).measure(self._size_text())

    def _draw_buttons(self) -> None:
        """The small buttons at the right of the top row.

        From the right: remove, lock, show or hide, timer.
        """
        self._remove_button = IconButton(
            self, self._button_x(0), px(TOP_ROW_Y), REMOVE_ICON, theme.FONT
        )

    def _button_x(self, place: int) -> int:
        """The middle of a button. `place` counts the buttons from the right, from 0."""
        size = px(IconButton.SIZE)
        step = size + px(BUTTON_GAP)  # from the middle of one button to the middle of the next
        return self._width - px(BUTTONS_RIGHT_PAD) - size // 2 - place * step
