"""The mirrors on the screen."""

import tkinter as tk
from collections.abc import Sequence

from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.overlay2.mirror_window import MirrorWindow


class MirrorManager:
    """Owns the mirror windows."""

    def __init__(self, window: tk.Misc, settings: AppSettingsStore) -> None:
        self._window = window
        self._settings = settings
        self._mirror_windows: list[MirrorWindow] = []

    def show(self, mirrors: Sequence[MirrorSettings], game_window: GameWindow) -> None:
        """Show a window for each of the mirrors, on the given window of Tibia.

        They replace the mirrors that were shown before.
        """
        self.close()

        for mirror_settings in mirrors:
            mirror_window = MirrorWindow(self._window, mirror_settings, game_window)
            self._mirror_windows.append(mirror_window)

    def close(self) -> None:
        """Close all mirror windows."""
        for mirror_window in self._mirror_windows:
            mirror_window.destroy()

        self._mirror_windows.clear()
