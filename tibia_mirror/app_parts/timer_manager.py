"""The timers that count."""

from tibia_mirror.app_parts.profile_manager import ProfileManager
from tibia_mirror.app_parts.tibia_connection import TibiaConnection
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.mirror_timer import MirrorTimer
from tibia_mirror.core.regions import size_key
from tibia_mirror.core.timers import combo_matches, pauses_of
from tibia_mirror.settings.app_settings_store import AppSettingsStore


class TimerManager:
    """Keeps when each timer started, by the id of its mirror."""

    def __init__(
        self,
        settings: AppSettingsStore,
        profile_manager: ProfileManager,
        connection: TibiaConnection,
    ) -> None:
        self._settings = settings
        self._profile_manager = profile_manager
        self._connection = connection
        self._start_times: dict[str, float] = {}  # mirror id -> when its timer started

    def start_by_key(self, key_code: int, modifiers: tuple[str, ...], now: float) -> None:
        """Start the timers of the open profile that this key starts, or start them again."""
        for mirror_settings in self._profile_manager.current.mirrors:
            timer = mirror_settings.timer

            if self._can_start(timer) and combo_matches(timer.key, key_code, modifiers):
                self._start_times[mirror_settings.mirror_id] = now

    def start_by_click(
        self, game_window: GameWindow, position_x: int, position_y: int, now: float
    ) -> None:
        """Start the timers of the open profile whose area of the game has this screen point."""
        client_area = game_window.client_area
        game_size_key = size_key(client_area.w, client_area.h)
        point_x = position_x - client_area.x
        point_y = position_y - client_area.y

        for mirror_settings in self._profile_manager.current.mirrors:
            layout = mirror_settings.layouts.get(game_size_key)
            is_clicked = layout is not None and layout.region.contains(point_x, point_y)

            if self._can_start(mirror_settings.timer) and is_clicked:
                self._start_times[mirror_settings.mirror_id] = now

    def continue_timers(self, now: float) -> None:
        """Start the timers of the character who logged in from their saved spots, if any.

        Without a login, nothing happens.
        """
        character = self._connection.character

        if character is None:
            return

        saved_times = pauses_of(self._settings.current.timer_pauses, character)

        for mirror_settings in self._profile_manager.current.mirrors:
            seconds = saved_times.get(mirror_settings.mirror_id)

            if seconds is not None:
                self._start_times[mirror_settings.mirror_id] = now - seconds

        self._settings.update(last_character=character)

    def stop(self, mirror_id: str) -> None:
        """Stop the timer of this mirror, so it shows its start time again."""
        self._start_times.pop(mirror_id, None)

    def stop_all(self) -> None:
        """Stop every timer, so each one shows its start time again."""
        self._start_times.clear()

    def get_elapsed(self, mirror_id: str, now: float) -> float | None:
        """Seconds since the timer of this mirror started. None if it has not started."""
        start_time = self._start_times.get(mirror_id)

        if start_time is None:
            return None

        return now - start_time

    def _can_start(self, timer: MirrorTimer) -> bool:
        """Whether this timer can start now. A timer that pauses while logged out needs a login."""
        is_logged_in = self._connection.character is not None

        return timer.is_on and (is_logged_in or not timer.is_paused_offline)
