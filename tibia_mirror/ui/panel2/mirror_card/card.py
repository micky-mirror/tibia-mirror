"""The card of one mirror on the Mirrors page."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import elide
from tibia_mirror.ui.panel2.mirror_card.button_bar import MirrorCardButtonBar
from tibia_mirror.ui.panel2.mirror_card.layout import BUTTONS_ROOM, TOP_ROW_Y
from tibia_mirror.ui.panel2.mirror_card.slider import MirrorCardSlider
from tibia_mirror.ui.panel2.mirror_card.text_link import TextLink
from tibia_mirror.ui.panel2.mirror_info import MirrorInfo

# Sizes at 100% display scaling; px() scales them where they are used.
HEIGHT = 62
RADIUS = 8  # of the rounded corners
DOT_X = 18  # from the left side of the card to the middle of the colour dot
DOT_SIZE = 10
NAME_X = 33  # from the left side of the card to the start of the name
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
        self._button_bar = MirrorCardButtonBar(self, self._width, self._mirror)
        self._slider = MirrorCardSlider(self, self._width, self._mirror)
        # the parts of the card: each one hears what the mouse does
        self._parts = (self._button_bar, self._slider)
        self._bind_events()

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
        position_x = self._name_end_x + px(TEXT_GAP)

        self._size_link = TextLink(self, position_x, px(TOP_ROW_Y), self._size_text())

    def _size_text(self) -> str:
        return f"{self._mirror.area_width}×{self._mirror.area_height}"

    def _size_width(self) -> int:
        """The width of the size text on the screen, in pixels."""
        return tkfont.Font(font=theme.FONT).measure(self._size_text())

    def _bind_events(self) -> None:
        # <Enter> too: the pointer can come in and stop, with no <Motion> after it.
        self.bind("<Enter>", self._on_mouse_move)
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_mouse_move(self, event: tk.Event[tk.Canvas]) -> None:
        """Tell the parts where the pointer is. Show a hand over a place that can be clicked."""
        positions = event.x, event.y
        is_clickable: bool = self._hover_size_link(*positions)

        for part in self._parts:
            if part.pointer_moved(*positions):
                is_clickable = True

        cursor = "hand2" if is_clickable else ""

        self.configure(cursor=cursor)

    def _on_mouse_leave(self, event: tk.Event[tk.Canvas]) -> None:
        self._size_link.set_hovered(False)

        for part in self._parts:
            part.pointer_left()

        self.configure(cursor="")

    def _on_mouse_down(self, event: tk.Event[tk.Canvas]) -> None:
        for part in self._parts:
            part.pointer_pressed(event.x, event.y)

    def _on_mouse_up(self, event: tk.Event[tk.Canvas]) -> None:
        """Tell the parts, and look at the place under the pointer again."""
        for part in self._parts:
            part.pointer_released(event.x, event.y)

        self._on_mouse_move(event)

    def _hover_size_link(self, position_x: int, position_y: int) -> bool:
        """Show the hover look of the size link when this place is on it. Return True if it is."""
        is_over_link: bool = self._size_link.contains(position_x, position_y)
        self._size_link.set_hovered(is_over_link)
        return is_over_link
