"""The timer manager: which timers start, and how long they have counted."""

from dataclasses import replace
from types import SimpleNamespace

from tibia_mirror.app_parts.timer_manager import TimerManager
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.mirror_timer import MirrorTimer
from tibia_mirror.core.profile import Profile

F1 = (112, ())  # a hotkey as the app keeps it: (key code, modifiers held with it)
F2 = (113, ())
ON_WITH_F1 = MirrorTimer(is_on=True, key=F1)  # a timer that its key F1 starts


def make_mirror(name, timer):
    return MirrorSettings(mirror_id=name, name=name, layouts={}, timer=timer)


def make_manager(mirrors):
    """A timer manager whose open profile has these mirrors."""
    profile_manager = SimpleNamespace(current=Profile(mirrors=tuple(mirrors)))
    return TimerManager(profile_manager)


def test_a_timer_that_has_not_started_has_no_time():
    manager = make_manager([make_mirror("Minimap", ON_WITH_F1)])

    assert manager.get_elapsed("Minimap", now=10.0) is None


def test_its_key_starts_a_timer():
    manager = make_manager([make_mirror("Minimap", ON_WITH_F1)])

    manager.start_by_key(*F1, now=10.0)

    assert manager.get_elapsed("Minimap", now=15.0) == 5.0


def test_another_key_starts_nothing():
    manager = make_manager([make_mirror("Minimap", ON_WITH_F1)])

    manager.start_by_key(*F2, now=10.0)

    assert manager.get_elapsed("Minimap", now=15.0) is None


def test_the_key_of_a_timer_that_is_off_starts_nothing():
    manager = make_manager([make_mirror("Minimap", replace(ON_WITH_F1, is_on=False))])

    manager.start_by_key(*F1, now=10.0)

    assert manager.get_elapsed("Minimap", now=15.0) is None


def test_its_key_starts_a_counting_timer_again():
    manager = make_manager([make_mirror("Minimap", ON_WITH_F1)])
    manager.start_by_key(*F1, now=10.0)

    manager.start_by_key(*F1, now=20.0)

    assert manager.get_elapsed("Minimap", now=25.0) == 5.0


def test_a_stopped_timer_has_no_time():
    manager = make_manager([make_mirror("Minimap", ON_WITH_F1), make_mirror("Health", ON_WITH_F1)])
    manager.start_by_key(*F1, now=10.0)

    manager.stop("Minimap")

    assert manager.get_elapsed("Minimap", now=15.0) is None
    assert manager.get_elapsed("Health", now=15.0) == 5.0


def test_stop_all_stops_every_timer():
    manager = make_manager([make_mirror("Minimap", ON_WITH_F1), make_mirror("Health", ON_WITH_F1)])
    manager.start_by_key(*F1, now=10.0)

    manager.stop_all()

    assert manager.get_elapsed("Minimap", now=15.0) is None
    assert manager.get_elapsed("Health", now=15.0) is None
