"""The timers that are running.

A mirror can have a timer. Some timers pause while no character is logged in.
RunningTimers remembers who is logged in, and when each of these timers started.

The paused progress (how far each paused timer got) is saved in the settings,
so RunningTimers reads and changes it there.
"""

from __future__ import annotations

from tibia_mirror.core.timers import (
    Pauses,
    button_matches,
    key_matches,
    pauses_of,
    with_pauses,
    without_mirrors,
)
from tibia_mirror.services.mirrors import Mirrors
from tibia_mirror.services.settings_store import SettingsStore
from tibia_mirror.ui.overlay.mirror import MirrorWindow


class RunningTimers:
    def __init__(self, settings: SettingsStore, mirrors: Mirrors) -> None:
        self._settings = settings
        self._mirrors = mirrors
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

    def set_online(self, character: str | None, now: float) -> None:
        """A character logged in, or logged out (then `character` is None)."""
        if self.online is not None:
            self._pause_timers(self.online, now)
        self.online = character
        self.started_at = {}
        if character is not None:
            self._continue_timers(character, now)
        for mirror in self._mirrors:
            self.sync(mirror, now)

    def _pause_timers(self, character: str, now: float) -> None:
        """`character` logs out: save how far each of its running timers got."""
        elapsed = {mirror_id: now - start for mirror_id, start in self.started_at.items()}
        self._save_pauses(with_pauses(self._settings.current.timer_pauses, character, elapsed))
        self.last_online = character
        if character != self._settings.current.last_character:
            self._settings.update(last_character=character)

    def _continue_timers(self, character: str, now: float) -> None:
        """`character` logs in: its paused timers run again."""
        paused = pauses_of(self._settings.current.timer_pauses, character)
        # A start time in the past makes the timer go on from its saved progress.
        self.started_at = {mirror_id: now - seconds for mirror_id, seconds in paused.items()}
        # The timers run again, so the paused progress of this character is removed.
        self._save_pauses(with_pauses(self._settings.current.timer_pauses, character, {}))

    def _save_pauses(self, pauses: Pauses) -> None:
        """Write the paused progress to the settings, if it is different."""
        if pauses != self._settings.current.timer_pauses:
            self._settings.update(timer_pauses=pauses)

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
        self._save_pauses(without_mirrors(self._settings.current.timer_pauses, {mirror.id}))

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

    def click(self, button: str, x: int, y: int, at: float) -> None:
        """A mouse button was pressed on the game.

        `x` and `y` are the point inside the client area of the game.
        Start every timer that this button starts, if its region has this point.
        """
        for mirror in self._mirrors:
            timer = mirror.timer
            if timer.enabled and button_matches(timer, button) and mirror.rect.contains(x, y):
                self.start(mirror, at)

    def key(self, vk: int, modifiers: tuple[str, ...], at: float) -> None:
        """A key was pressed while the game was in front. Start every timer that uses this key."""
        for mirror in self._mirrors:
            if mirror.timer.enabled and key_matches(mirror.timer, vk, modifiers):
                self.start(mirror, at)

    def tick(self, now: float) -> list[str]:
        """Update every timer.

        Return the sounds to play: one for each timer that reached its alert time just now.
        """
        return [mirror.timer.sound for mirror in self._mirrors if mirror.tick_timer(now)]
