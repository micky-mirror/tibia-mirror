"""The card of one mirror on the Mirrors page."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from tibia_mirror.config import MIN_OPACITY, OPACITY_STEP
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.text import elide, percent
from tibia_mirror.ui.controls.slider import SliderDrawing
from tibia_mirror.ui.panel2.icon_button import IconButton
from tibia_mirror.ui.panel2.mirror_info import MirrorInfo

REMOVE_ICON = "✕"
LOCKED_ICON = "\ue72e"  # a closed lock, from the Segoe MDL2 Assets icon font
UNLOCKED_ICON = "\ue785"  # an open lock, from the same font
SHOWN_ICON = "\ue890"  # an open eye, from the same font
HIDDEN_ICON = "\ued1a"  # a crossed eye, from the same font
TIMER_ICON = "\ue916"  # a clock, from the same font

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
SLIDER_Y = 44  # from the top of the card to the middle line of the slider
SLIDER_SIDE_PAD = 14  # from the left side of the card to the slider
PERCENT_ROOM = 48  # kept free between the slider and the right side space, for the percent


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
        self._is_dragging = False  # True from a press on the slider until the button goes up
        self._draw_background()
        self._draw_colour_dot()
        self._draw_name()
        self._draw_size()
        self._draw_buttons()
        self._draw_slider()
        self._draw_percent()
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
        self._draw_remove_button()
        self._draw_lock_button()
        self._draw_eye_button()
        self._draw_timer_button()
        self._buttons = (
            self._remove_button,
            self._lock_button,
            self._eye_button,
            self._timer_button,
        )

    def _draw_remove_button(self) -> None:
        self._remove_button = IconButton(
            self,
            self._button_position_x(0),
            px(TOP_ROW_Y),
            REMOVE_ICON,
            theme.FONT,
            theme.SUBTEXT,
            theme.RED,
        )

    def _draw_lock_button(self) -> None:
        """A closed lock in the accent colour for a locked mirror, an open grey lock if not."""
        is_locked: bool = self._mirror.is_locked
        icon = LOCKED_ICON if is_locked else UNLOCKED_ICON
        colour = theme.ACCENT if is_locked else theme.SUBTEXT
        hovered_colour = theme.ACCENT if is_locked else theme.TEXT

        self._lock_button = IconButton(
            self,
            self._button_position_x(1),
            px(TOP_ROW_Y),
            icon,
            theme.FONT_ICON,
            colour,
            hovered_colour,
        )

    def _draw_eye_button(self) -> None:
        """A crossed eye in the accent colour for a hidden mirror, an open grey eye if not."""
        is_hidden: bool = self._mirror.is_hidden
        icon = HIDDEN_ICON if is_hidden else SHOWN_ICON
        colour = theme.ACCENT if is_hidden else theme.SUBTEXT
        hovered_colour = theme.ACCENT if is_hidden else theme.TEXT

        self._eye_button = IconButton(
            self,
            self._button_position_x(2),
            px(TOP_ROW_Y),
            icon,
            theme.FONT_ICON,
            colour,
            hovered_colour,
        )

    def _draw_timer_button(self) -> None:
        """A clock, in the accent colour for a mirror with its timer on, grey if not."""
        is_timer_on: bool = self._mirror.is_timer_on
        colour = theme.ACCENT if is_timer_on else theme.SUBTEXT
        hovered_colour = theme.ACCENT if is_timer_on else theme.TEXT

        self._timer_button = IconButton(
            self,
            self._button_position_x(3),
            px(TOP_ROW_Y),
            TIMER_ICON,
            theme.FONT_ICON,
            colour,
            hovered_colour,
        )

    def _button_position_x(self, place: int) -> int:
        """The middle of a button. `place` counts the buttons from the right, from 0."""
        size = px(IconButton.SIZE)
        step = size + px(BUTTON_GAP)  # from the middle of one button to the middle of the next
        return self._width - px(BUTTONS_RIGHT_PAD) - size // 2 - place * step

    def _draw_slider(self) -> None:
        """The slider under the top row that sets how see-through the mirror is."""
        position_x_start = px(SLIDER_SIDE_PAD)
        position_x_end = self._width - px(SLIDER_SIDE_PAD) - px(PERCENT_ROOM)

        self._slider = SliderDrawing(
            self,
            position_x_start,
            position_x_end,
            px(SLIDER_Y),
            self._mirror.opacity,
            lo=0.0,
            hi=1.0,
            step=OPACITY_STEP,
            floor=MIN_OPACITY,
        )

    def _draw_percent(self) -> None:
        """The opacity as a percent, at the right of the slider."""
        self._percent = self.create_text(
            self._width - px(SLIDER_SIDE_PAD),
            px(SLIDER_Y),
            text=percent(self._mirror.opacity),
            anchor="e",
            font=theme.FONT,
            fill=theme.SUBTEXT,
        )

    def _bind_events(self) -> None:
        # <Enter> too: the pointer can come in and stop, with no <Motion> after it.
        self.bind("<Enter>", self._on_mouse_move)
        self.bind("<Motion>", self._on_mouse_move)
        self.bind("<Leave>", self._on_mouse_leave)
        self.bind("<ButtonPress-1>", self._on_mouse_down)
        self.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _on_mouse_move(self, event: tk.Event[tk.Canvas]) -> None:
        """Move the knob while the user drags it.

        With no drag, show the hover look of the part under the pointer, and a hand over it.
        """
        if self._is_dragging:
            self._move_knob(event.x)
            return

        positions = event.x, event.y
        is_over_button: bool = self._hover_buttons(*positions)
        is_over_slider: bool = self._hover_slider(*positions)

        is_clickable: bool = is_over_button or is_over_slider
        cursor = "hand2" if is_clickable else ""

        self.configure(cursor=cursor)

    def _on_mouse_leave(self, event: tk.Event[tk.Canvas]) -> None:
        for button in self._buttons:
            button.set_hovered(False)

        # a drag goes on outside the card, and the knob stays active until it ends
        if not self._is_dragging:
            self._slider.set_active(False)
        self.configure(cursor="")

    def _on_mouse_down(self, event: tk.Event[tk.Canvas]) -> None:
        """Start a drag if the button went down on the slider: the knob jumps to the pointer."""
        if self._slider.contains(event.x, event.y):
            self._is_dragging = True
            self._move_knob(event.x)

    def _on_mouse_up(self, event: tk.Event[tk.Canvas]) -> None:
        """End the drag, and look at the place under the pointer again."""
        self._is_dragging = False
        self._on_mouse_move(event)

    def _move_knob(self, position_x: int) -> None:
        """Put the knob as near to this x as the steps and the lowest value allow.

        Show the new opacity as a percent too. Do nothing when the opacity did not change.
        """
        opacity = self._slider.value_at(position_x)
        if opacity == self._slider.value:
            return

        self._slider.set_value(opacity)
        self.itemconfigure(self._percent, text=percent(opacity))

    def _hover_buttons(self, position_x: int, position_y: int) -> bool:
        """Show the hover look of the button at this place. Return True if there is one."""
        is_over_button: bool = False

        for button in self._buttons:
            is_hovered: bool = button.contains(position_x, position_y)
            button.set_hovered(is_hovered)
            if is_hovered:
                is_over_button = True

        return is_over_button

    def _hover_slider(self, position_x: int, position_y: int) -> bool:
        """Show the knob as active when this place is on the slider. Return True if it is."""
        is_over_slider: bool = self._slider.contains(position_x, position_y)
        self._slider.set_active(is_over_slider)
        return is_over_slider
