"""Timer helpers: key combinations, clock text, alert times and paused progress per character."""

from typing import TypeGuard

from tibia_mirror.config import TIMER_ALERT_RANGE

# Modifier keys a timer's key can be combined with, in the order they are written.
MODIFIERS = ("ctrl", "shift", "alt")
MODIFIER_NAMES = {"ctrl": "Ctrl", "shift": "Shift", "alt": "Alt"}

# A key combination: a Windows virtual-key code and the modifiers held with it,
# from MODIFIERS in their order, e.g. (120, ("shift",)) for Shift+F9.
KeyCombo = tuple[int, tuple[str, ...]]


def _is_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def parse_key(value: object) -> int | None:
    """A Windows virtual-key code read from a file, or None if `value` is not one."""
    return value if _is_int(value) and 0 < value < 256 else None


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


def clock(seconds: int) -> str:
    """Whole seconds as mm:ss, at most 59:59."""
    minutes, secs = divmod(max(0, min(seconds, 59 * 60 + 59)), 60)
    return f"{minutes:02d}:{secs:02d}"


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
