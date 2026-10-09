"""The timers that are running.

A mirror can have a timer. Some timers pause while no character is logged in.
RunningTimers remembers who is logged in, and when each of these timers started.

The paused progress (how far each paused timer got) is saved in the settings,
so RunningTimers reads and changes it there.
"""

from __future__ import annotations

from tibia_mirror.core.timers import pauses_of, without_mirrors
from tibia_mirror.services.settings_store import SettingsStore
from tibia_mirror.ui.overlay.mirror import MirrorWindow


class RunningTimers:
    def __init__(self, settings: SettingsStore) -> None:
        self._settings = settings
        # The character that is logged in to Tibia now. None if nobody is logged in.
        # It changes at once on a login or logout, so the timers lose no time.
        self.online: str | None = None
        # The character that was logged in last. While nobody is logged in, the app
        # shows the paused timers of this character. It is saved for the next start.
        self.last_online: str | None = settings.current.last_character or None
        # Mirror id -> the time when its timer started.
        # Only for timers that pause while logged out, and only for `online`.
        # It can hold mirrors of other profiles too.
        # It is lost if the app closes while a character is logged in.
        self.started_at: dict[str, float] = {}

    def start(self, mirror: MirrorWindow, at: float) -> None:
        """Start the timer of `mirror` at the time `at`.

        A timer that pauses while logged out only counts while a character is logged in.
        So if nobody is logged in, such a timer does not start.
        """
        if mirror.timer.pauses_offline:
            if self.online is None:
                return
            self.started_at[mirror.id] = at
        mirror.start_timer(at)

    def forget(self, mirror: MirrorWindow) -> None:
        """Drop the progress of the timer of `mirror`, for every character.

        Call it when the mirror is removed, or when its timer gets new settings.
        """
        self.started_at.pop(mirror.id, None)
        pauses = without_mirrors(self._settings.current.timer_pauses, {mirror.id})
        if pauses != self._settings.current.timer_pauses:
            self._settings.update(timer_pauses=pauses)

    def sync(self, mirror: MirrorWindow, now: float) -> None:
        """Make the timer of `mirror` show the right state for who is logged in.

        This is only for timers that pause while logged out. Other timers are not touched.

        There are three cases:
        - A character is logged in: the timer runs from its start time.
          If it has no start time, it shows as not started.
        - Nobody is logged in, but someone was before: the timer shows the paused
          progress of that character.
        - Nobody was logged in yet: the timer shows as not started.
        """
        if not mirror.timer.pauses_offline:
            return
        if self.online is not None:
            mirror.restore_timer(now, started=self.started_at.get(mirror.id))
        elif self.last_online is not None:
            pauses = pauses_of(self._settings.current.timer_pauses, self.last_online)
            mirror.restore_timer(now, paused=pauses.get(mirror.id))
        else:
            mirror.restore_timer(now)
