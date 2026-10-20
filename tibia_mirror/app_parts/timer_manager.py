"""The timers that count."""

from tibia_mirror.app_parts.profile_manager import ProfileManager
from tibia_mirror.core.timers import combo_matches


class TimerManager:
    """Keeps when each timer started, by the id of its mirror."""

    def __init__(self, profile_manager: ProfileManager) -> None:
        self._profile_manager = profile_manager
        self._start_times: dict[str, float] = {}  # mirror id -> when its timer started

    def start_by_key(self, key_code: int, modifiers: tuple[str, ...], now: float) -> None:
        """Start the timers of the open profile that this key starts, or start them again."""
        for mirror_settings in self._profile_manager.current.mirrors:
            timer = mirror_settings.timer

            if timer.is_on and combo_matches(timer.key, key_code, modifiers):
                self._start_times[mirror_settings.mirror_id] = now

    def get_elapsed(self, mirror_id: str, now: float) -> float | None:
        """Seconds since the timer of this mirror started. None if it has not started."""
        start_time = self._start_times.get(mirror_id)

        if start_time is None:
            return None

        return now - start_time
