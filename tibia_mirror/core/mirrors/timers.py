"""Timer helpers: clock text, alert times and paused progress per character."""

from tibia_mirror.config import TIMER_ALERT_RANGE


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
