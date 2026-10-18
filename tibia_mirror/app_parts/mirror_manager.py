"""The mirrors on the screen."""

import tkinter as tk
from dataclasses import replace

from tibia_mirror.app_parts.profile_manager import ProfileManager
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.mirror_look import MirrorLook
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.regions import size_key
from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.overlay2.mirror_window import MirrorWindow
from tibia_mirror.ui.panel2.mirror_info import MirrorInfo


class MirrorManager:
    """Owns the mirror windows."""

    def __init__(
        self,
        window: tk.Misc,
        settings: AppSettingsStore,
        profile_manager: ProfileManager,
    ) -> None:
        self._window = window
        self._settings = settings
        self._profile_manager = profile_manager
        self._mirror_windows: list[MirrorWindow] = []

    def show(self, game_window: GameWindow) -> int:
        """Show a window for each kept mirror, on the given window of Tibia.

        They replace the mirror windows shown before. A mirror that Windows refuses
        to draw gets no window, but it is still kept. Returns how many got no window.
        """
        self.close()
        mirror_look = self._get_mirror_look()
        failed = 0

        for mirror_settings in self._profile_manager.current.mirrors:
            try:
                mirror_window = MirrorWindow(
                    self._window,
                    mirror_settings,
                    game_window,
                    mirror_look,
                    self._profile_manager.update_mirror,
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

    def update_windows(self) -> None:
        """Make every mirror window follow the open profile after it changed.

        Each window gets the settings of its mirror. The window of a removed mirror closes.
        """
        kept_windows: list[MirrorWindow] = []

        for mirror_window in self._mirror_windows:
            mirror_settings = self._get_mirror(mirror_window.mirror_id)

            if mirror_settings is None:
                mirror_window.destroy()
            else:
                mirror_window.set_mirror_settings(mirror_settings)
                kept_windows.append(mirror_window)

        self._mirror_windows = kept_windows

    def close(self) -> None:
        """Close all mirror windows. The mirrors are still kept."""
        for mirror_window in self._mirror_windows:
            mirror_window.destroy()

        self._mirror_windows.clear()

    def get_mirror_infos(self, game_window: GameWindow) -> list[MirrorInfo]:
        """What the Mirrors page shows about each kept mirror, for this size of the game."""
        client_area = game_window.client_area
        game_size_key = size_key(client_area.w, client_area.h)
        mirror_infos: list[MirrorInfo] = []

        for mirror_settings in self._profile_manager.current.mirrors:
            layout = mirror_settings.layouts.get(game_size_key)

            if layout is None:
                continue

            mirror_infos.append(
                MirrorInfo(
                    mirror_id=mirror_settings.mirror_id,
                    name=mirror_settings.name,
                    area_width=layout.region.w,
                    area_height=layout.region.h,
                    opacity=mirror_settings.opacity,
                    colour=mirror_settings.colour,
                    is_hidden=mirror_settings.is_hidden,
                    is_locked=mirror_settings.is_locked,
                    timer=mirror_settings.timer,
                )
            )

        return mirror_infos

    def update_mirror(self, mirror_info: MirrorInfo) -> None:
        """Put a change from the Mirrors page into the open profile."""
        mirror_settings = self._get_mirror(mirror_info.mirror_id)

        if mirror_settings is None:
            return

        new_settings = replace(
            mirror_settings,
            is_hidden=mirror_info.is_hidden,
            is_locked=mirror_info.is_locked,
            colour=mirror_info.colour,
            opacity=mirror_info.opacity,
            timer=mirror_info.timer,
        )

        self._profile_manager.update_mirror(new_settings)

    def _get_mirror(self, mirror_id: str) -> MirrorSettings | None:
        """The kept mirror with this id. None if there is none."""
        for mirror_settings in self._profile_manager.current.mirrors:
            if mirror_settings.mirror_id == mirror_id:
                return mirror_settings

        return None

    def _get_mirror_look(self) -> MirrorLook:
        """The look every mirror window shares, from the app settings."""
        current = self._settings.current

        return MirrorLook(
            is_frame_on=current.is_mirror_frame_on,
            is_rounded_on=current.is_rounded_corners_on,
            is_tint_on=current.is_frame_tint_on,
        )
