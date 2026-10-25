"""The frame over the picture of the loupe that marks one game pixel."""

import tkinter as tk

from tibia_mirror.core.geometry import Point
from tibia_mirror.ui.base.windows import keep_open
from tibia_mirror.winapi import win32

SEE_THROUGH = "#ff00fe"  # Windows leaves the pixels of this colour out, so the picture shows
# A white line on a wider black one, so the frame shows on every colour of the game.
# The widths stay the same at any display scaling, as in the old loupe.
OUTLINES = (("#000000", 3), ("#ffffff", 1))


class PixelMarker(tk.Toplevel):
    """A see-through window over the picture of the loupe, with a frame around one pixel."""

    def __init__(self, parent: tk.Misc, picture_size: int, pixel_size: int) -> None:
        super().__init__(parent, bg=SEE_THROUGH)
        self.withdraw()  # hidden until the loupe shows it
        self._pixel_size = pixel_size  # one game pixel in the picture, in screen pixels
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        self.attributes("-topmost", True)  # above the picture of the loupe
        # only the selection overlay closes it
        keep_open(self)
        self.geometry(f"{picture_size}x{picture_size}")
        # window layer setup
        self.attributes("-transparentcolor", SEE_THROUGH)
        win32.set_click_through(win32.toplevel_hwnd(self), True)
        # the frame around the pixel
        self._canvas = self._add_canvas(picture_size)
        self._outlines = self._add_outlines()

    def show_at(self, picture_position: Point, pixel_position: Point) -> None:
        """Lie over the picture at this place, and frame the pixel at this place in it."""
        picture_x, picture_y = picture_position
        pixel_x, pixel_y = pixel_position
        pixel_end_x, pixel_end_y = pixel_x + self._pixel_size, pixel_y + self._pixel_size
        frame_box = (pixel_x - 2, pixel_y - 2, pixel_end_x + 1, pixel_end_y + 1)

        for outline in self._outlines:
            self._canvas.coords(outline, *frame_box)

        self.geometry(f"+{picture_x}+{picture_y}")
        self.deiconify()

    def _add_canvas(self, picture_size: int) -> tk.Canvas:
        canvas = tk.Canvas(
            self,
            width=picture_size,
            height=picture_size,
            bg=SEE_THROUGH,
            highlightthickness=0,
        )
        canvas.pack()
        return canvas

    def _add_outlines(self) -> list[int]:
        """The black line first, so the white one lies on top of it."""
        return [
            self._canvas.create_rectangle(0, 0, 0, 0, outline=colour, width=line_width)
            for colour, line_width in OUTLINES
        ]
