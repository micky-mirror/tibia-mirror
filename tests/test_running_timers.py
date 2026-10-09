from dataclasses import replace

import pytest

from tibia_mirror.core.timers import TimerSettings
from tibia_mirror.services.running_timers import RunningTimers
from tibia_mirror.services.settings_store import SettingsStore

PAUSING = TimerSettings(enabled=True, alert=60, direction="down")
PLAIN = replace(PAUSING, offline_pause=False)


class FakeMirror:
    """Stands in for a mirror window: it has an id and a timer, and records its start."""

    def __init__(self, mirror_id, timer):
        self.id = mirror_id
        self.timer = timer
        self.started = None
        self.restored = None

    def start_timer(self, at):
        self.started = at

    def restore_timer(self, now, started=None, paused=None):
        self.restored = (now, started, paused)


@pytest.fixture
def settings(tmp_path):
    return SettingsStore(tmp_path / "settings.json", lambda: None)


@pytest.fixture
def mirrors():
    return []


@pytest.fixture
def timers(settings, mirrors):
    return RunningTimers(settings, mirrors)


def test_last_online_comes_from_the_settings(settings):
    assert RunningTimers(settings, []).last_online is None
    settings.update(last_character="Knight")
    assert RunningTimers(settings, []).last_online == "Knight"


def test_a_plain_timer_starts_also_when_nobody_is_logged_in(timers):
    mirror = FakeMirror("m1", PLAIN)
    timers.start(mirror, 5.0)
    assert mirror.started == 5.0
    assert timers.started_at == {}


def test_a_pausing_timer_does_not_start_when_nobody_is_logged_in(timers):
    mirror = FakeMirror("m1", PAUSING)
    timers.start(mirror, 5.0)
    assert mirror.started is None
    assert timers.started_at == {}


def test_a_pausing_timer_starts_and_is_remembered_when_someone_is_logged_in(timers):
    timers.online = "Knight"
    mirror = FakeMirror("m1", PAUSING)
    timers.start(mirror, 5.0)
    assert mirror.started == 5.0
    assert timers.started_at == {"m1": 5.0}


def test_forget_drops_the_start_time_and_the_paused_progress(timers, settings):
    settings.update(timer_pauses=(("Knight", "m1", 12.5), ("Knight", "m2", 3.0)))
    timers.started_at = {"m1": 1.0}
    timers.forget(FakeMirror("m1", PAUSING))
    assert timers.started_at == {}
    assert settings.current.timer_pauses == (("Knight", "m2", 3.0),)


def test_sync_does_not_touch_a_plain_timer(timers):
    mirror = FakeMirror("m1", PLAIN)
    timers.sync(mirror, 10.0)
    assert mirror.restored is None


def test_sync_shows_a_running_timer_while_someone_is_logged_in(timers):
    timers.online = "Knight"
    timers.started_at = {"m1": 4.0}
    running, not_started = FakeMirror("m1", PAUSING), FakeMirror("m2", PAUSING)
    timers.sync(running, 10.0)
    timers.sync(not_started, 10.0)
    assert running.restored == (10.0, 4.0, None)
    assert not_started.restored == (10.0, None, None)


def test_sync_shows_the_paused_progress_of_who_was_logged_in_last(settings):
    settings.update(timer_pauses=(("Knight", "m1", 12.5),), last_character="Knight")
    mirror = FakeMirror("m1", PAUSING)
    RunningTimers(settings, []).sync(mirror, 10.0)
    assert mirror.restored == (10.0, None, 12.5)


def test_sync_shows_not_started_when_nobody_was_logged_in_yet(timers):
    mirror = FakeMirror("m1", PAUSING)
    timers.sync(mirror, 10.0)
    assert mirror.restored == (10.0, None, None)


def test_a_login_with_nothing_paused_only_sets_who_is_online(timers, settings):
    timers.set_online("Knight", 10.0)
    assert timers.online == "Knight"
    assert timers.started_at == {}
    assert settings.current.timer_pauses == ()


def test_a_logout_saves_how_far_each_running_timer_got(timers, settings):
    timers.online = "Knight"
    timers.started_at = {"m1": 4.0}
    timers.set_online(None, 10.0)
    assert timers.online is None
    assert timers.started_at == {}
    assert settings.current.timer_pauses == (("Knight", "m1", 6.0),)
    assert timers.last_online == "Knight"
    assert settings.current.last_character == "Knight"


def test_a_login_continues_the_paused_timers_of_that_character(timers, settings):
    settings.update(timer_pauses=(("Knight", "m1", 6.0),))
    timers.set_online("Knight", 20.0)
    assert timers.started_at == {"m1": 14.0}
    assert settings.current.timer_pauses == ()


def test_the_paused_timers_of_another_character_are_kept(timers, settings):
    settings.update(timer_pauses=(("Druid", "m9", 3.0), ("Knight", "m1", 6.0)))
    timers.set_online("Knight", 20.0)
    assert settings.current.timer_pauses == (("Druid", "m9", 3.0),)


def test_a_change_from_one_character_to_another_pauses_and_continues(timers, settings):
    settings.update(timer_pauses=(("Druid", "m9", 3.0),))
    timers.online = "Knight"
    timers.started_at = {"m1": 4.0}
    timers.set_online("Druid", 10.0)
    assert settings.current.timer_pauses == (("Knight", "m1", 6.0),)
    assert timers.started_at == {"m9": 7.0}
    assert timers.last_online == "Knight"


def test_after_a_logout_every_mirror_shows_its_paused_progress(timers, mirrors):
    mirror = FakeMirror("m1", PAUSING)
    mirrors.append(mirror)
    timers.online = "Knight"
    timers.started_at = {"m1": 4.0}
    timers.set_online(None, 10.0)
    assert mirror.restored == (10.0, None, 6.0)
