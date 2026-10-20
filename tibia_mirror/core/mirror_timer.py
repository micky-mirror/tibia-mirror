"""The timer of one mirror."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from tibia_mirror.config import TIMER_ALERT_RANGE, TIMER_DIRECTIONS
from tibia_mirror.core.timers import KeyCombo, canonical_modifiers, clock, parse_key

# the sounds a timer can play; the first is the default
SOUNDS = ("notification", "critical", "beep", "none")


@dataclass(frozen=True)
class MirrorTimer:
    is_on: bool = False
    alert_seconds: int = 60  # the alert comes this long after the start, within TIMER_ALERT_RANGE
    direction: str = TIMER_DIRECTIONS[0]  # "down" or "up"
    key: KeyCombo | None = None  # the key that also starts the timer. None: no key is set
    sound: str = SOUNDS[0]  # the name of the sound played when the time is up
    is_paused_offline: bool = True  # the timer counts only while the character is logged in

    @classmethod
    def from_json(cls, data: object) -> MirrorTimer:
        """Make the timer from its part of a profile file."""
        saved = _SavedTimer(data)

        return cls(
            is_on=saved.get_bool("enabled", default=cls.is_on),
            alert_seconds=saved.get_alert_seconds(),
            direction=saved.get_choice("direction", TIMER_DIRECTIONS),
            key=saved.get_key_combo(),
            sound=saved.get_choice("sound", SOUNDS),
            is_paused_offline=saved.get_bool("offline_pause", default=cls.is_paused_offline),
        )

    def to_json(self) -> dict[str, Any]:
        """The timer as it is written to a profile file."""
        key_code, modifiers = self.key or (None, ())

        return {
            "enabled": self.is_on,
            "alert": self.alert_seconds,
            "direction": self.direction,
            "key": key_code,
            "modifiers": list(modifiers),
            "sound": self.sound,
            "offline_pause": self.is_paused_offline,
        }

    def get_start_text(self) -> str:
        """The time on the badge before the timer starts, for example "01:00"."""
        return self.get_text(0)

    def get_text(self, elapsed: float) -> str:
        """The time on the badge this many seconds after the start, for example "00:42".

        It stops at the alert time. Counting down rounds up, so it shows "00:01" until the end.
        """
        counted = min(elapsed, self.alert_seconds)

        if self.direction == "down":
            return clock(math.ceil(self.alert_seconds - counted))

        return clock(math.floor(counted))

    def is_done(self, elapsed: float) -> bool:
        """Whether the alert time has come this many seconds after the start."""
        return elapsed >= self.alert_seconds


class _SavedTimer:
    """The timer of a mirror in a profile file, with one method for each kind of value.

    A value that is missing or wrong in the file is replaced by its default.
    """

    def __init__(self, data: object) -> None:
        # Content that is not a JSON object is read as an empty one.
        self._data: dict[str, Any] = data if isinstance(data, dict) else {}

    def get_bool(self, name: str, *, default: bool) -> bool:
        """The saved value if it is true or false. If not, the default."""
        value = self._data.get(name)

        if isinstance(value, bool):
            return value

        return default

    def get_alert_seconds(self) -> int:
        """The saved whole number of seconds if it is in the allowed range. If not, the default."""
        value = self._data.get("alert")
        shortest, longest = TIMER_ALERT_RANGE

        if type(value) is int and shortest <= value <= longest:
            return value

        return MirrorTimer.alert_seconds

    def get_choice(self, name: str, choices: tuple[str, ...]) -> str:
        """The saved text if it is one of the choices. If not, the first choice."""
        value = self._data.get(name)

        if isinstance(value, str) and value in choices:
            return value

        return choices[0]

    def get_key_combo(self) -> KeyCombo | None:
        """The saved key with the modifiers held with it. None if no key is saved."""
        key_code = parse_key(self._data.get("key"))
        modifiers = canonical_modifiers(self._data.get("modifiers"))

        if key_code is None:
            return None

        return key_code, modifiers
