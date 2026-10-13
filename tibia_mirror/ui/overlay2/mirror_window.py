"""One mirror on the screen."""

import tkinter as tk

from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import scaled_size
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.regions import Layout, size_key
from tibia_mirror.ui.base.windows import keep_open


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
        self._show_at_saved_place()

    def _show_at_saved_place(self) -> None:
        """Show the window with the size and the place from its layout.

        A mirror without a layout for this size of the game stays hidden.
        """
        layout = self._get_layout()

        if layout is None:
            return

        client_area = self._game_window.client_area
        zoom = self._mirror_settings.zoom
        area_width, area_height = scaled_size(layout.region.w, layout.region.h, zoom)
        position_x = client_area.x + layout.offset[0]
        position_y = client_area.y + layout.offset[1]

        self.geometry(f"{area_width}x{area_height}+{position_x}+{position_y}")
        self.deiconify()
        self.attributes("-topmost", True)  # above other windows, also above the game

    def _get_layout(self) -> Layout | None:
        """The saved layout for this size of the game. None if there is none."""
        client_area = self._game_window.client_area
        size = size_key(client_area.w, client_area.h)

        return self._mirror_settings.layouts.get(size)
