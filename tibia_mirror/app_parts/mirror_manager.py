"""The mirrors on the screen."""

import time
import tkinter as tk
from dataclasses import replace

from tibia_mirror.app_parts.profile_manager import ProfileManager
from tibia_mirror.app_parts.tibia_connection import TibiaConnection
from tibia_mirror.app_parts.timer_manager import TimerManager
from tibia_mirror.config import NEW_MIRROR_GAP
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import Point, Rect, place_beside
from tibia_mirror.core.mirror_look import MirrorLook
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.regions import Layout, new_id, size_key
from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.overlay.mirror_window import MirrorWindow
from tibia_mirror.ui.panel.mirrors.mirror_info import MirrorInfo
from tibia_mirror.winapi import win32


class MirrorManager:
    """Owns the mirror windows."""

    def __init__(
        self,
        window: tk.Misc,
        settings: AppSettingsStore,
        profile_manager: ProfileManager,
        timer_manager: TimerManager,
        connection: TibiaConnection,
    ) -> None:
        self._window = window
        self._settings = settings
        self._profile_manager = profile_manager
        self._timer_manager = timer_manager
        self._connection = connection
        self._mirror_windows: list[MirrorWindow] = []

    def show(self) -> int:
        """Show a window for each kept mirror, on the window of Tibia if there is one.

        They replace the mirror windows shown before. A mirror that Windows refuses
        to draw gets no window, but it is still kept. Returns how many got no window.
        """
        self.close()
        game_window = self._connection.game_window

        if game_window is None:
            return 0

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

    def update_timer_badges(self, now: float) -> None:
        """Show on every mirror window how long its timer has counted."""
        for mirror_window in self._mirror_windows:
            elapsed = self._timer_manager.get_elapsed(mirror_window.mirror_id, now)
            mirror_window.set_timer_elapsed(elapsed)

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

    def get_mirror_infos(self) -> list[MirrorInfo] | None:
        """What the Mirrors page shows about each kept mirror. None without a window of Tibia."""
        game_window = self._connection.game_window

        if game_window is None:
            return None

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

    def add_mirror(self, name: str, area: Rect) -> None:
        """Add a mirror of this part of the game to the open profile."""
        game_window = self._connection.game_window

        if game_window is None:
            return

        client_area = game_window.client_area
        layout = Layout(area, self._get_new_mirror_offset(area, client_area))
        mirror_settings = MirrorSettings(
            mirror_id=new_id(),
            name=name,
            layouts={size_key(client_area.w, client_area.h): layout},
            opacity=self._settings.current.new_mirror_opacity,
        )

        self._profile_manager.add_mirror(mirror_settings)

    def set_area(self, mirror_id: str, area: Rect) -> None:
        """Let the mirror show this part of the game, for the size the game has now."""
        mirror_settings = self._get_mirror(mirror_id)
        game_window = self._connection.game_window

        if mirror_settings is None or game_window is None:
            return

        client_area = game_window.client_area
        game_size_key = size_key(client_area.w, client_area.h)
        layout = mirror_settings.layouts.get(game_size_key)
        # the mirror stays where it is; without a place for this size it goes beside the area
        offset = self._get_new_mirror_offset(area, client_area) if layout is None else layout.offset
        layouts = {**mirror_settings.layouts, game_size_key: Layout(area, offset)}

        self._profile_manager.update_mirror(replace(mirror_settings, layouts=layouts))

    def update_mirror(self, mirror_info: MirrorInfo) -> None:
        """Put a change from the Mirrors page into the open profile.

        A hotkey that is new for the timer is first cleared from every place that has it.
        New timer settings stop the timer, so it starts over.
        """
        mirror_settings = self._get_mirror(mirror_info.mirror_id)

        if mirror_settings is None:
            return

        new_settings = replace(
            mirror_settings,
            name=mirror_info.name,
            is_hidden=mirror_info.is_hidden,
            is_locked=mirror_info.is_locked,
            colour=mirror_info.colour,
            opacity=mirror_info.opacity,
            timer=mirror_info.timer,
        )
        hotkey = new_settings.timer.key

        if hotkey is not None and hotkey != mirror_settings.timer.key:
            self._profile_manager.clear_hotkey(hotkey)

        self._stop_changed_timer(mirror_settings, new_settings)
        self._profile_manager.update_mirror(new_settings)

    def _stop_changed_timer(
        self, mirror_settings: MirrorSettings, new_settings: MirrorSettings
    ) -> None:
        """Stop the timer of this mirror when its timer settings change."""
        if new_settings.timer == mirror_settings.timer:
            return

        self._timer_manager.stop(mirror_settings.mirror_id)
        self.update_timer_badges(time.monotonic())

    def _get_new_mirror_offset(self, area: Rect, client_area: Rect) -> Point:
        """Where a new mirror sits: beside the part of the game it shows, on the same screen."""
        area_on_screen = Rect(client_area.x + area.x, client_area.y + area.y, area.w, area.h)
        center = (area_on_screen.x + area.w // 2, area_on_screen.y + area.h // 2)
        work_area = win32.work_area_at(center)
        gap = px(NEW_MIRROR_GAP)

        mirror_x, mirror_y = place_beside(area_on_screen, area.w, area.h, work_area, gap)
        return mirror_x - client_area.x, mirror_y - client_area.y

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
