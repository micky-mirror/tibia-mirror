"""The timer manager: which timers start, and how long they have counted."""

from dataclasses import replace
from types import SimpleNamespace

from tibia_mirror.app_parts.timer_manager import TimerManager
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.mirror_timer import MirrorTimer
from tibia_mirror.core.profile import Profile
from tibia_mirror.core.regions import Layout
from tibia_mirror.settings.app_settings import AppSettings

F1 = (112, ())  # a hotkey as the app keeps it: (key code, modifiers held with it)
F2 = (113, ())
# a timer that its key F1 starts, also while nobody is logged in
ON_WITH_F1 = MirrorTimer(is_on=True, key=F1, is_paused_offline=False)
PAUSING_WITH_F1 = replace(ON_WITH_F1, is_paused_offline=True)  # counts only while logged in
GAME_WINDOW = GameWindow(100, Rect(10, 20, 800, 600), is_minimized=False, is_in_front=True)
AREA = Layout(Rect(5, 5, 320, 64), (0, 0))  # the area of the mirror, inside the game


class FakeSettingsStore:
    """Stands in for the settings store. It keeps the settings in memory only."""

    def __init__(self, **values):
        self.current = AppSettings(**values)

    def update(self, **new_values):
        self.current = replace(self.current, **new_values)


def make_mirror(name, timer):
    return MirrorSettings(mirror_id=name, name=name, layouts={}, timer=timer)


def make_shown_mirror(name, timer):
    """A mirror with an area for the size of GAME_WINDOW, so a click on that area can start it."""
    return replace(make_mirror(name, timer), layouts={"800x600": AREA})


def make_profile_manager(mirrors):
    """Stands in for the profile manager. The open profile has these mirrors."""
    return SimpleNamespace(current=Profile(mirrors=tuple(mirrors)))


def make_manager(mirrors, character=None):
    """A timer manager whose open profile has these mirrors, while this character is logged in."""
    settings_store = SimpleNamespace(current=AppSettings())
    connection = SimpleNamespace(character=character)
    return TimerManager(settings_store, make_profile_manager(mirrors), connection)


def change_character(manager, connection, character, now):
    """Log in or out the way the app does: pause the timers first, then continue them."""
    connection.character = character
    manager.pause_timers(now)
    manager.continue_timers(now)


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


def test_a_click_on_its_area_starts_a_timer():
    manager = make_manager([make_shown_mirror("Minimap", ON_WITH_F1)])

    manager.start_by_click(GAME_WINDOW, 20, 30, now=10.0)

    assert manager.get_elapsed("Minimap", now=15.0) == 5.0


def test_a_click_outside_its_area_starts_nothing():
    manager = make_manager([make_shown_mirror("Minimap", ON_WITH_F1)])

    manager.start_by_click(GAME_WINDOW, 500, 400, now=10.0)

    assert manager.get_elapsed("Minimap", now=15.0) is None


def test_a_click_is_measured_from_the_corner_of_the_game():
    # (12, 22) is on the area when measured from the corner of the screen, but not from the game
    manager = make_manager([make_shown_mirror("Minimap", ON_WITH_F1)])

    manager.start_by_click(GAME_WINDOW, 12, 22, now=10.0)

    assert manager.get_elapsed("Minimap", now=15.0) is None


def test_a_click_on_the_area_of_a_timer_that_is_off_starts_nothing():
    manager = make_manager([make_shown_mirror("Minimap", replace(ON_WITH_F1, is_on=False))])

    manager.start_by_click(GAME_WINDOW, 20, 30, now=10.0)

    assert manager.get_elapsed("Minimap", now=15.0) is None


def test_a_mirror_without_an_area_for_this_size_of_the_game_starts_nothing():
    other_size = replace(make_mirror("Minimap", ON_WITH_F1), layouts={"1024x768": AREA})
    manager = make_manager([other_size])

    manager.start_by_click(GAME_WINDOW, 20, 30, now=10.0)

    assert manager.get_elapsed("Minimap", now=15.0) is None


def test_a_pausing_timer_does_not_start_while_nobody_is_logged_in():
    manager = make_manager([make_shown_mirror("Minimap", PAUSING_WITH_F1)])

    manager.start_by_key(*F1, now=10.0)
    manager.start_by_click(GAME_WINDOW, 20, 30, now=10.0)

    assert manager.get_elapsed("Minimap", now=15.0) is None


def test_a_pausing_timer_starts_while_a_character_is_logged_in():
    manager = make_manager([make_mirror("Minimap", PAUSING_WITH_F1)], character="Knight")

    manager.start_by_key(*F1, now=10.0)

    assert manager.get_elapsed("Minimap", now=15.0) == 5.0


def test_a_logout_stops_a_pausing_timer_at_its_spot():
    connection = SimpleNamespace(character=None)
    profile_manager = make_profile_manager([make_mirror("Minimap", PAUSING_WITH_F1)])
    manager = TimerManager(FakeSettingsStore(), profile_manager, connection)
    change_character(manager, connection, "Knight", now=0.0)
    manager.start_by_key(*F1, now=10.0)

    change_character(manager, connection, None, now=25.0)

    assert manager.get_elapsed("Minimap", now=100.0) == 15.0


def test_a_logout_does_not_stop_a_timer_that_does_not_pause():
    connection = SimpleNamespace(character=None)
    profile_manager = make_profile_manager([make_mirror("Minimap", ON_WITH_F1)])
    manager = TimerManager(FakeSettingsStore(), profile_manager, connection)
    change_character(manager, connection, "Knight", now=0.0)
    manager.start_by_key(*F1, now=10.0)

    change_character(manager, connection, None, now=25.0)

    assert manager.get_elapsed("Minimap", now=100.0) == 90.0


def test_a_logout_saves_the_spot_beside_the_other_spots_of_the_character():
    settings_store = FakeSettingsStore(timer_pauses=(("Knight", "Health", 7.0),))
    connection = SimpleNamespace(character=None)
    profile_manager = make_profile_manager([make_mirror("Minimap", PAUSING_WITH_F1)])
    manager = TimerManager(settings_store, profile_manager, connection)
    change_character(manager, connection, "Knight", now=0.0)
    manager.start_by_key(*F1, now=10.0)

    change_character(manager, connection, None, now=25.0)

    expected_pauses = (("Knight", "Health", 7.0), ("Knight", "Minimap", 15.0))
    assert settings_store.current.timer_pauses == expected_pauses


def test_the_saved_spot_shows_when_the_app_starts_on_the_login_screen():
    settings_store = FakeSettingsStore(
        last_character="Knight", timer_pauses=(("Knight", "Minimap", 15.0),)
    )
    profile_manager = make_profile_manager([make_mirror("Minimap", PAUSING_WITH_F1)])
    manager = TimerManager(settings_store, profile_manager, SimpleNamespace(character=None))

    assert manager.get_elapsed("Minimap", now=100.0) == 15.0


def test_a_login_continues_a_timer_from_its_saved_spot():
    settings_store = FakeSettingsStore(timer_pauses=(("Knight", "Minimap", 15.0),))
    connection = SimpleNamespace(character=None)
    profile_manager = make_profile_manager([make_mirror("Minimap", PAUSING_WITH_F1)])
    manager = TimerManager(settings_store, profile_manager, connection)

    change_character(manager, connection, "Knight", now=100.0)

    assert manager.get_elapsed("Minimap", now=103.0) == 18.0


def test_a_login_does_not_continue_the_spot_of_another_character():
    settings_store = FakeSettingsStore(timer_pauses=(("Druid", "Minimap", 15.0),))
    connection = SimpleNamespace(character=None)
    profile_manager = make_profile_manager([make_mirror("Minimap", PAUSING_WITH_F1)])
    manager = TimerManager(settings_store, profile_manager, connection)

    change_character(manager, connection, "Knight", now=100.0)

    assert manager.get_elapsed("Minimap", now=103.0) is None
