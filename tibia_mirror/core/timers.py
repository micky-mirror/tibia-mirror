"""Mirror timers: their settings, what the badge shows, and paused progress per
character. Pure logic, unit-tested; see docs/architecture.md, "Input and timers".
"""

import math
from dataclasses import dataclass
from typing import Any, TypeGuard

from tibia_mirror.config import TIMER_ALERT_RANGE, TIMER_BUTTONS, TIMER_DIRECTIONS, TIMER_SOUNDS

# Modifier keys a timer's key can be combined with, in the order they are written.
MODIFIERS = ("ctrl", "shift", "alt")
MODIFIER_NAMES = {"ctrl": "Ctrl", "shift": "Shift", "alt": "Alt"}

# A key combination: a Windows virtual-key code and the modifiers held with it,
# from MODIFIERS in their order, e.g. (120, ("shift",)) for Shift+F9.
KeyCombo = tuple[int, tuple[str, ...]]


@dataclass(frozen=True)
class TimerSettings:
    enabled: bool = False
    alert: int = 60  # seconds, within TIMER_ALERT_RANGE
    direction: str = TIMER_DIRECTIONS[0]  # "down" or "up"
    button: str = TIMER_BUTTONS[0]  # which mouse button on the region starts it
    key: int | None = None  # Windows virtual-key code that also starts it
    sound: str = TIMER_SOUNDS[0]
    modifiers: tuple[str, ...] = ()  # held with the key, from MODIFIERS, e.g. ("shift",)
    offline_pause: bool = True  # pauses while the character is logged out

    @property
    def combo(self) -> KeyCombo | None:
        """The key and its modifiers, or None if the timer has no key."""
        return None if self.key is None else (self.key, self.modifiers)

    def to_json(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "alert": self.alert,
            "direction": self.direction,
            "button": self.button,
            "key": self.key,
            "modifiers": list(self.modifiers),
            "sound": self.sound,
            "offline_pause": self.offline_pause,
        }

    @classmethod
    def from_json(cls, data: object) -> "TimerSettings":
        """Settings from a profile file; anything missing or invalid falls back to its default."""
        if not isinstance(data, dict):
            return cls()
        default = cls()
        lo, hi = TIMER_ALERT_RANGE
        alert = data.get("alert")
        return cls(
            enabled=data.get("enabled") is True,
            alert=alert if _is_int(alert) and lo <= alert <= hi else default.alert,
            direction=_one_of(data.get("direction"), TIMER_DIRECTIONS),
            button=_one_of(data.get("button"), TIMER_BUTTONS),
            key=parse_key(data.get("key")),
            sound=_one_of(data.get("sound"), TIMER_SOUNDS),
            modifiers=canonical_modifiers(data.get("modifiers")),
            offline_pause=_bool(data.get("offline_pause"), default.offline_pause),
        )

    @property
    def pauses_offline(self) -> bool:
        return self.enabled and self.offline_pause


def _is_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _bool(value: object, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def parse_key(value: object) -> int | None:
    """A Windows virtual-key code read from a file, or None if `value` is not one."""
    return value if _is_int(value) and 0 < value < 256 else None


def _one_of(value: object, choices: tuple[str, ...]) -> str:
    return value if isinstance(value, str) and value in choices else choices[0]


def canonical_modifiers(names: object) -> tuple[str, ...]:
    """Known modifier names, each once, in MODIFIERS order (anything else is dropped)."""
    names = names if isinstance(names, list | tuple | set | frozenset) else ()
    return tuple(modifier for modifier in MODIFIERS if modifier in names)


def combo_name(modifiers: tuple[str, ...], key_name: str) -> str:
    """How a key combination is written, e.g. "Ctrl+Shift+F9"."""
    names = [MODIFIER_NAMES[modifier] for modifier in canonical_modifiers(modifiers)]
    return "+".join([*names, key_name])


def combo_matches(combo: KeyCombo | None, vk: int, modifiers: tuple[str, ...]) -> bool:
    """Whether pressing `vk` with exactly `modifiers` held is `combo` (None matches nothing)."""
    return combo is not None and combo == (vk, canonical_modifiers(modifiers))


def key_matches(settings: TimerSettings, vk: int, modifiers: tuple[str, ...]) -> bool:
    """Whether pressing `vk` with exactly `modifiers` held starts this timer."""
    return combo_matches(settings.combo, vk, modifiers)


def key_clashes(settings: TimerSettings, combo: KeyCombo | None) -> bool:
    """Whether this timer is on and started by `combo`: a key may start one thing only."""
    return settings.enabled and combo is not None and key_matches(settings, *combo)


def clock(seconds: int) -> str:
    """Whole seconds as mm:ss, at most 59:59."""
    minutes, secs = divmod(max(0, min(seconds, 59 * 60 + 59)), 60)
    return f"{minutes:02d}:{secs:02d}"


def badge_text(settings: TimerSettings, elapsed: float | None) -> str:
    """The badge's text `elapsed` seconds after the start (None: not started yet).

    Counting down rounds up, so it reads 00:01 until the very end.
    """
    down = settings.direction == "down"
    if elapsed is None:
        return clock(settings.alert if down else 0)
    elapsed = min(elapsed, settings.alert)
    if down:
        return clock(math.ceil(settings.alert - elapsed))
    return clock(math.floor(elapsed))


def is_done(settings: TimerSettings, elapsed: float | None) -> bool:
    return elapsed is not None and elapsed >= settings.alert


def button_matches(settings: TimerSettings, button: str) -> bool:
    """Whether a click with `button` ("left" or "right") starts this timer."""
    return settings.button in ("both", button)


def parse_alert(minutes: str, seconds: str) -> int | None:
    """Alert time in seconds from the dialog's fields, or None if it is outside the range."""
    if not (minutes.isdigit() and seconds.isdigit()):
        return None
    total = int(minutes) * 60 + int(seconds)
    lo, hi = TIMER_ALERT_RANGE
    return total if lo <= total <= hi and int(seconds) < 60 else None


# Paused progress of timers that pause while logged out: sorted (character,
# mirror id, seconds counted) entries, so it fits in the frozen Settings.
Pauses = tuple[tuple[str, str, float], ...]


def pauses_of(pauses: Pauses, character: str) -> dict[str, float]:
    """The character's paused timers: mirror id -> seconds counted."""
    return {mirror: seconds for who, mirror, seconds in pauses if who == character}


def with_pauses(pauses: Pauses, character: str, elapsed: dict[str, float]) -> Pauses:
    """`pauses` with the character's entries replaced by `elapsed` (mirror id -> seconds)."""
    kept = [pause for pause in pauses if pause[0] != character]
    added = [(character, mirror, round(seconds, 1)) for mirror, seconds in elapsed.items()]
    return tuple(sorted(kept + added))


def without_mirrors(pauses: Pauses, mirrors: set[str]) -> Pauses:
    return tuple(pause for pause in pauses if pause[1] not in mirrors)


def pauses_from_json(data: object) -> Pauses:
    """From settings.json's {"character": {"mirror id": seconds}}; anything else is dropped."""
    if not isinstance(data, dict):
        return ()
    pauses: Pauses = ()
    for character, timers in data.items():
        if not isinstance(timers, dict):
            continue
        elapsed = {
            str(mirror): float(seconds)
            for mirror, seconds in timers.items()
            if isinstance(seconds, int | float) and not isinstance(seconds, bool) and seconds >= 0
        }
        pauses = with_pauses(pauses, character, elapsed)
    return pauses


def pauses_to_json(pauses: Pauses) -> dict[str, dict[str, float]]:
    data: dict[str, dict[str, float]] = {}
    for character, mirror, elapsed in pauses:
        data.setdefault(character, {})[mirror] = elapsed
    return data
