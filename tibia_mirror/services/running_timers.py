"""The timers that are running.

A mirror can have a timer. Some timers pause while no character is logged in.
RunningTimers remembers who is logged in, and when each of these timers started.
"""

from __future__ import annotations


class RunningTimers:
    def __init__(self, last_online: str | None) -> None:
        # The character that is logged in to Tibia now. None if nobody is logged in.
        # It changes at once on a login or logout, so the timers lose no time.
        self.online: str | None = None
        # The character that was logged in last. While nobody is logged in, the app
        # shows the paused timers of this character. It is saved for the next start.
        self.last_online = last_online
        # Mirror id -> the time when its timer started.
        # Only for timers that pause while logged out, and only for `online`.
        # It can hold mirrors of other profiles too.
        # It is lost if the app closes while a character is logged in.
        self.started_at: dict[str, float] = {}
