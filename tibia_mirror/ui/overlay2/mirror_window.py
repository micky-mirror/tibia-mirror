"""One mirror on the screen."""

import tkinter as tk

from tibia_mirror.config import COLOR_BORDER, FRAME_COLORS, MIRROR_BORDER
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import Rect, scaled_size
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.core.mirror_look import MirrorLook
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.regions import Layout, size_key
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.base.windows import keep_open
from tibia_mirror.ui.overlay2.mirror_frame import MirrorFrame
from tibia_mirror.winapi import dwm, win32
from tibia_mirror.winapi.dwm import Thumbnail


class MirrorWindow(tk.Toplevel):
    """A window that shows a part of the game."""

    def __init__(
        self,
        parent: tk.Misc,
        mirror_settings: MirrorSettings,
        game_window: GameWindow,
        mirror_look: MirrorLook,
    ) -> None:
        super().__init__(parent)
        self.withdraw()  # hidden until it has a size and a place
        self._mirror_settings = mirror_settings
        self._game_window = game_window
        self._mirror_look = mirror_look
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        # only the app closes a mirror
        keep_open(self)
        # the number Windows knows this window by
        self._window_handle: Hwnd = win32.toplevel_hwnd(self)
        # window layer setup
        win32.set_alpha(self._window_handle, mirror_settings.opacity)
        win32.set_click_through(self._window_handle, mirror_settings.is_locked)
        # the frame behind a rounded picture
        self._mirror_frame = MirrorFrame(self, mirror_settings.opacity)
        # initialize thumbnail connection
        self._thumbnail = self._create_thumbnail()
        # render window at given place
        self._show_at_saved_place()

    def destroy(self) -> None:
        """Stop the thumbnail and close the window."""
        self._thumbnail.close()
        super().destroy()

    def set_game_window(self, game_window: GameWindow) -> None:
        """Follow the window of Tibia after it changed."""
        self._game_window = game_window
        self._show_at_saved_place()

    def set_mirror_look(self, mirror_look: MirrorLook) -> None:
        """Draw the window with a new look."""
        self._mirror_look = mirror_look
        self._show_at_saved_place()

    def _show_at_saved_place(self) -> None:
        """Show the window at its saved place, or hide it when it must not be shown."""
        layout = self._get_layout()
        is_tibia_in_use = self._game_window.is_in_front and not self._game_window.is_minimized

        if layout is None or self._mirror_settings.is_hidden or not is_tibia_in_use:
            self._mirror_frame.withdraw()
            self.withdraw()
            return

        picture_area = self._get_picture_area(layout)
        border = self._get_border_width()
        window_margin = 0 if self._mirror_look.is_rounded_on else border

        window_area = picture_area.grown(window_margin)
        thumbnail_area = Rect(window_margin, window_margin, picture_area.w, picture_area.h)

        dwm.set_rounded_corners(self._window_handle, self._mirror_look.is_rounded_on)
        self._show_frame_window(picture_area, border)
        # shows as the frame around the picture
        self.configure(bg=theme.frame_color(self._mirror_settings.colour))
        self.geometry(f"{window_area.w}x{window_area.h}+{window_area.x}+{window_area.y}")
        self._thumbnail.show(layout.region, thumbnail_area)
        self.deiconify()
        self.attributes("-topmost", True)  # above other windows, also above the game

    def _get_picture_area(self, layout: Layout) -> Rect:
        """Where the picture of the game goes on the screen."""
        client_area = self._game_window.client_area
        zoom = self._mirror_settings.zoom
        area_width, area_height = scaled_size(layout.region.w, layout.region.h, zoom)
        position_x = client_area.x + layout.offset[0]
        position_y = client_area.y + layout.offset[1]

        return Rect(position_x, position_y, area_width, area_height)

    def _get_border_width(self) -> int:
        """The width of the frame around the picture."""
        is_coloured = self._mirror_settings.colour != FRAME_COLORS[0]

        if is_coloured:
            return px(COLOR_BORDER)

        if self._mirror_look.is_frame_on:
            return px(MIRROR_BORDER)

        return 0

    def _show_frame_window(self, picture_area: Rect, border: int) -> None:
        """Show the frame window around a rounded picture, or hide it."""
        is_frame_window_used = self._mirror_look.is_rounded_on and border > 0

        if not is_frame_window_used:
            self._mirror_frame.withdraw()
            return

        self._mirror_frame.show(picture_area, border, self._mirror_settings.colour)

    def _get_layout(self) -> Layout | None:
        """The saved layout for this size of the game. None if there is none."""
        client_area = self._game_window.client_area
        size = size_key(client_area.w, client_area.h)

        return self._mirror_settings.layouts.get(size)

    def _create_thumbnail(self) -> Thumbnail:
        """Ask Windows to draw a live copy of the game into this window.

        If Windows refuses, the window is closed and this raises OSError.
        """
        try:
            return Thumbnail(self._window_handle, self._game_window.handle)
        except OSError:
            super().destroy()
            raise
