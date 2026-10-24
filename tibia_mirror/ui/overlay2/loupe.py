"""The magnifier of the selection overlay."""

import tkinter as tk

from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import Point, Rect, magnifier_source
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.windows import keep_open
from tibia_mirror.winapi import win32
from tibia_mirror.winapi.dwm import Thumbnail


class Loupe(tk.Toplevel):
    """A small window beside the pointer that shows the game under it, bigger."""

    SPAN = 11  # game pixels across; odd, so the pixel of the point is the middle one
    # sizes at 100% display scaling
    ZOOM = 6  # screen pixels for each game pixel
    OFFSET = 28  # between the pointer and the loupe
    TEXT_HEIGHT = 20  # the line under the picture with the size of the box

    def __init__(self, parent: tk.Misc, game_window: GameWindow) -> None:
        super().__init__(parent, bg=theme.BG)
        self.withdraw()  # hidden until it has a place
        self._game_window = game_window
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        self.attributes("-topmost", True)  # above the game and the selection overlay
        # only the selection overlay closes it
        keep_open(self)
        picture_size = self.SPAN * px(self.ZOOM)
        self._width = picture_size
        self._height = picture_size + px(self.TEXT_HEIGHT)
        self.geometry(f"{self._width}x{self._height}")
        # the size of the box, under the picture
        self._size_label = self._add_size_label(picture_size)
        # the number Windows knows this window by
        self._window_handle: Hwnd = win32.toplevel_hwnd(self)
        # window layer setup
        win32.set_alpha(self._window_handle, 1.0)
        win32.set_click_through(self._window_handle, True)
        # initialize thumbnail connection
        self._thumbnail = Thumbnail(self._window_handle, game_window.handle)

    def destroy(self) -> None:
        """Stop the thumbnail and close the window."""
        self._thumbnail.close()
        super().destroy()

    def show_at(self, point: Point, box_size: tuple[int, int] = (0, 0)) -> None:
        """Show the game around this point of the screen, beside it."""
        client_area = self._game_window.client_area
        point_x, point_y = point
        game_x, game_y = point_x - client_area.x, point_y - client_area.y
        source = magnifier_source(game_x, game_y, self.SPAN, client_area.w, client_area.h)
        zoom = px(self.ZOOM)
        position_x, position_y = self._get_position(point)

        self._thumbnail.show(source, Rect(0, 0, source.w * zoom, source.h * zoom))
        self.geometry(f"+{position_x}+{position_y}")
        self._size_label.configure(text="{} × {}".format(*box_size))
        self.deiconify()

    def _add_size_label(self, picture_size: int) -> tk.Label:
        size_label = tk.Label(self, bg=theme.BG, fg=theme.TEXT, font=theme.FONT_SMALL)
        size_label.place(x=0, y=picture_size, width=picture_size, height=px(self.TEXT_HEIGHT))
        return size_label

    def _get_position(self, point: Point) -> Point:
        """Below and right of the point, or on the other side near the edges of its screen."""
        point_x, point_y = point
        work_area = win32.work_area_at(point)
        offset = px(self.OFFSET)
        position_x = point_x + offset
        position_y = point_y + offset

        if position_x + self._width > work_area.right:
            position_x = point_x - offset - self._width

        if position_y + self._height > work_area.bottom:
            position_y = point_y - offset - self._height

        return position_x, position_y
