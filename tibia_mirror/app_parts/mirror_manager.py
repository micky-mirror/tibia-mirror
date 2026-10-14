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
        self._is_visible = True

    def show(self, mirrors: Sequence[MirrorSettings], game_window: GameWindow) -> int:
        """Show a window for each of the mirrors, on the given window of Tibia.

        They replace the mirrors that were shown before. A mirror that Windows refuses
        to draw is left out. Returns how many were left out.
        """
        self.close()
        failed = 0

        for mirror_settings in mirrors:
            try:
                mirror_window = MirrorWindow(
                    self._window, mirror_settings, game_window, self._is_visible
                )
            except OSError:
                failed += 1
            else:
                self._mirror_windows.append(mirror_window)

        return failed

    def set_game_window(self, game_window: GameWindow) -> None:
        """Make every mirror window follow the window of Tibia after it moved or changed size."""
        for mirror_window in self._mirror_windows:
            mirror_window.set_game_window(game_window)

    def set_visible(self, is_visible: bool) -> None:
        """Show or hide every mirror window."""
        self._is_visible = is_visible

        for mirror_window in self._mirror_windows:
            mirror_window.set_visible(is_visible)

    def close(self) -> None:
        """Close all mirror windows."""
        for mirror_window in self._mirror_windows:
            mirror_window.destroy()

        self._mirror_windows.clear()
