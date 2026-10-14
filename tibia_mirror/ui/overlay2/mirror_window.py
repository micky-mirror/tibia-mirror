"""One mirror on the screen."""

import tkinter as tk

from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import Rect, scaled_size
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.regions import Layout, size_key
from tibia_mirror.ui.base.windows import keep_open
from tibia_mirror.winapi import win32
from tibia_mirror.winapi.dwm import Thumbnail


class MirrorWindow(tk.Toplevel):
    """A window that shows a part of the game."""

    def __init__(
        self,
        parent: tk.Misc,
        mirror_settings: MirrorSettings,
        game_window: GameWindow,
    ) -> None:
        super().__init__(parent)
        self.withdraw()  # hidden until it has a size and a place
        self._mirror_settings = mirror_settings
        self._game_window = game_window
        self.overrideredirect(True)  # no title bar and no borders
        keep_open(self)  # Alt+F4 does not close a mirror, only the app does
        # the number Windows knows this window by
        self._window_handle: Hwnd = win32.toplevel_hwnd(self)
        self._thumbnail = self._create_thumbnail()
        self._show_at_saved_place()

    def destroy(self) -> None:
        """Stop the thumbnail and close the window."""
        self._thumbnail.close()
        super().destroy()

    def set_game_window(self, game_window: GameWindow) -> None:
        """Follow the window of Tibia after it moved or changed size."""
        self._game_window = game_window
        self._show_at_saved_place()

    def _show_at_saved_place(self) -> None:
        """Show the window with the size and the place from its layout.

        A mirror without a layout for this size of the game is hidden.
        """
        layout = self._get_layout()

        if layout is None:
            self.withdraw()
            return

        client_area = self._game_window.client_area
        zoom = self._mirror_settings.zoom
        area_width, area_height = scaled_size(layout.region.w, layout.region.h, zoom)
        position_x = client_area.x + layout.offset[0]
        position_y = client_area.y + layout.offset[1]

        self.geometry(f"{area_width}x{area_height}+{position_x}+{position_y}")
        thumbnail_area = Rect(0, 0, area_width, area_height)
        self._thumbnail.show(layout.region, thumbnail_area)
        self.deiconify()
        self.attributes("-topmost", True)  # above other windows, also above the game

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
