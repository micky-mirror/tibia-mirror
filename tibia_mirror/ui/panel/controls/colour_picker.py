"""The colour picker: a small window with colour swatches, under the colour dot."""

from __future__ import annotations

import math
import tkinter as tk
from collections.abc import Callable

from tibia_mirror.core.geometry import Box
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import outlined_image, rounded_image
from tibia_mirror.ui.base.scale import px
from tibia_mirror.winapi import dwm, win32

# Sizes at 100% display scaling; px() scales them where they are used.
GAP = 4  # between the colour dot and the picker
PAD = 8  # around the swatches, inside the picker
SWATCH_SIZE = 18  # of one square swatch
SWATCH_RADIUS = 3  # of the rounded corners of a swatch
SWATCH_GAP = 8  # between two swatches
RING_GAP = 2.5  # between a swatch and the ring around it


class ColourPicker(tk.Toplevel):
    """The colours to pick from, as swatches in rows, in a small window."""

    def __init__(
        self,
        window: tk.Misc,
        colours: dict[str, str],
        selected: str,
        per_row: int,
        on_pick: Callable[[str], None],
    ) -> None:
        super().__init__(window, bg=theme.SURFACE)
        self.withdraw()  # hidden until it has a place
        self._window = window  # the window under the picker; it gets the focus back
        self._colours = colours  # the name and the hex code of each colour, in the order shown
        self._selected = selected  # the name of the chosen colour
        self._per_row = per_row  # how many swatches one row holds
        self._on_pick = on_pick  # called with the name of the colour the user picks
        self._swatch_images: list[tk.PhotoImage] = []  # Tk shows a picture only while it is kept
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        self.attributes("-topmost", True)  # above the panel, which can be on top too
        # rounded corners, a shadow and a thin border, all drawn by Windows
        dwm.round_popup(win32.toplevel_hwnd(self), theme.SURFACE_HI)
        # add picker content
        self._add_canvas()
        self._draw_swatches()
        self._bind_events()

    def open(self, box: Box) -> None:
        """Show the picker under `box`, from its left side. `box` is a place on the screen."""
        left, _top, _right, bottom = box
        position_y = bottom + px(GAP)

        self.geometry(f"+{left}+{position_y}")
        self.deiconify()
        self.grab_set()  # every click of the app comes to the picker
        self.focus_force()  # the Escape key comes to the picker

    def close(self) -> None:
        """Close the picker, and give the focus back to the window under it."""
        self.destroy()
        self._window.focus_force()

    def _add_canvas(self) -> None:
        """The surface the swatches are drawn on. It fills the whole picker."""
        width, height = self._get_size()

        self._canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg=theme.SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self._canvas.pack(fill="both", expand=True)

    def _draw_swatches(self) -> None:
        """Each colour as a round swatch, with a ring around the chosen one."""
        for index, (name, colour) in enumerate(self._colours.items()):
            box = self._get_swatch_box(index)

            if name == self._selected:
                self._draw_ring(box, colour)

            self._draw_swatch(box, colour)

    def _draw_swatch(self, box: Box, colour: str) -> None:
        size = px(SWATCH_SIZE)
        image = rounded_image(
            self._canvas,
            width=size,
            height=size,
            radius=px(SWATCH_RADIUS),
            colour=colour,
            background=theme.SURFACE,
        )
        left, top, _right, _bottom = box

        self._swatch_images.append(image)
        self._canvas.create_image(left, top, anchor="nw", image=image)

    def _draw_ring(self, box: Box, colour: str) -> None:
        """A thin ring in `colour` around the swatch of the chosen colour."""
        room = px(RING_GAP) + 1  # from the swatch to the outside of the 1px ring
        size = px(SWATCH_SIZE) + 2 * room
        left, top, _right, _bottom = box

        self._ring_image = outlined_image(
            self._canvas,
            width=size,
            height=size,
            radius=px(SWATCH_RADIUS) + room,  # the corners curve like the swatch's
            colour=theme.SURFACE,
            border=colour,
            background=theme.SURFACE,
        )
        self._canvas.create_image(left - room, top - room, anchor="nw", image=self._ring_image)

    def _get_size(self) -> tuple[int, int]:
        """Room for every swatch, with a pad around them."""
        columns = min(self._per_row, len(self._colours))
        rows = math.ceil(len(self._colours) / self._per_row)
        width = 2 * px(PAD) + columns * self._get_step() - px(SWATCH_GAP)
        height = 2 * px(PAD) + rows * self._get_step() - px(SWATCH_GAP)

        return width, height

    def _get_step(self) -> int:
        """From the start of one swatch to the start of the next one."""
        return px(SWATCH_SIZE) + px(SWATCH_GAP)

    def _get_swatch_box(self, index: int) -> Box:
        """The place of the swatch at `index` on the picker."""
        column = index % self._per_row
        row = index // self._per_row
        left = px(PAD) + column * self._get_step()
        top = px(PAD) + row * self._get_step()

        return left, top, left + px(SWATCH_SIZE), top + px(SWATCH_SIZE)

    def _get_name_at(self, position_x: int, position_y: int) -> str | None:
        """The colour whose swatch is at this place on the picker."""
        for index, name in enumerate(self._colours):
            left, top, right, bottom = self._get_swatch_box(index)
            is_inside_x = left <= position_x < right
            is_inside_y = top <= position_y < bottom

            if is_inside_x and is_inside_y:
                return name

        return None

    def _is_inside(self, position_x: int, position_y: int) -> bool:
        """Whether this place, measured from the top left corner of the picker, is on it."""
        is_inside_x = 0 <= position_x < self.winfo_width()
        is_inside_y = 0 <= position_y < self.winfo_height()

        return is_inside_x and is_inside_y

    def _bind_events(self) -> None:
        self.bind("<Escape>", self._on_escape)
        self.bind("<ButtonRelease>", self._on_mouse_up)
        self.bind("<FocusOut>", self._on_focus_out)
        self.protocol("WM_DELETE_WINDOW", self.close)  # Alt+F4

    def _on_escape(self, event: tk.Event[tk.Misc]) -> None:
        self.close()

    def _on_mouse_up(self, event: tk.Event[tk.Misc]) -> None:
        # the picker holds the grab, so every click of the app ends here
        position_x = event.x_root - self.winfo_rootx()
        position_y = event.y_root - self.winfo_rooty()
        name = self._get_name_at(position_x, position_y)

        if not self._is_inside(position_x, position_y):
            self.close()
        elif name is not None:
            self._pick(name)

    def _on_focus_out(self, event: tk.Event[tk.Misc]) -> None:
        # another app has the focus now, so the picker closes and leaves the focus there
        if event.widget is self:
            self.destroy()

    def _pick(self, name: str) -> None:
        """Close the picker, then hand over the name of the colour."""
        self.close()
        self._on_pick(name)
