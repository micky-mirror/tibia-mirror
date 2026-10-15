"""The mirrors on the screen."""

import tkinter as tk
from collections.abc import Callable, Sequence

from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.mirror_look import MirrorLook
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.overlay2.mirror_window import MirrorWindow


class MirrorManager:
    """Owns the mirror windows."""

    def __init__(
        self,
        window: tk.Misc,
        settings: AppSettingsStore,
        on_changed: Callable[[Sequence[MirrorSettings]], None],
    ) -> None:
        self._window = window
        self._settings = settings
        self._on_changed = on_changed
        self._mirrors: list[MirrorSettings] = []
        self._mirror_windows: list[MirrorWindow] = []

    def set_mirrors(self, mirrors: Sequence[MirrorSettings]) -> None:
        """Keep the mirrors of the open profile while the app runs."""
        self._mirrors = list(mirrors)

    def show(self, game_window: GameWindow) -> int:
        """Show a window for each kept mirror, on the given window of Tibia.

        They replace the mirror windows shown before. A mirror that Windows refuses
        to draw gets no window, but it is still kept. Returns how many got no window.
        """
        self.close()
        mirror_look = self._get_mirror_look()
        failed = 0

        for mirror_settings in self._mirrors:
            try:
                mirror_window = MirrorWindow(
                    self._window,
                    mirror_settings,
                    game_window,
                    mirror_look,
                    self._on_mirror_changed,
                )
            except OSError:
                failed += 1
            else:
                self._mirror_windows.append(mirror_window)

        return failed

    def set_game_window(self, game_window: GameWindow) -> None:
        """Make every mirror window follow the window of Tibia after it changed."""
        for mirror_window in self._mirror_windows:
            mirror_window.set_game_window(game_window)

    def update_mirror_look(self) -> None:
        """Give every mirror window the look from the current app settings."""
        mirror_look = self._get_mirror_look()

        for mirror_window in self._mirror_windows:
            mirror_window.set_mirror_look(mirror_look)

    def close(self) -> None:
        """Close all mirror windows. The mirrors are still kept."""
        for mirror_window in self._mirror_windows:
            mirror_window.destroy()

        self._mirror_windows.clear()

    def _on_mirror_changed(self, mirror_settings: MirrorSettings) -> None:
        """Keep the new settings of a changed mirror, and pass all mirrors on."""
        for index, kept_settings in enumerate(self._mirrors):
            if kept_settings.mirror_id == mirror_settings.mirror_id:
                self._mirrors[index] = mirror_settings

        self._on_changed(list(self._mirrors))

    def _get_mirror_look(self) -> MirrorLook:
        """The look every mirror window shares, from the app settings."""
        current = self._settings.current

        return MirrorLook(
            is_frame_on=current.is_mirror_frame_on,
            is_rounded_on=current.is_rounded_corners_on,
            is_tint_on=current.is_frame_tint_on,
        )
