"""The mirror manager: which mirror windows it shows and closes."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from tibia_mirror.app_parts import mirror_manager as mirror_manager_module
from tibia_mirror.app_parts.mirror_manager import MirrorManager
from tibia_mirror.app_parts.timer_manager import TimerManager
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.mirror_look import MirrorLook
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.mirror_timer import MirrorTimer
from tibia_mirror.core.profile import Profile
from tibia_mirror.core.regions import Layout
from tibia_mirror.settings.app_settings import AppSettings
from tibia_mirror.ui.panel2.mirror_info import MirrorInfo

GAME_WINDOW = GameWindow(100, Rect(10, 20, 800, 600), is_minimized=False, is_in_front=True)
DEFAULT_SETTINGS = AppSettings()
F1 = (112, ())  # a hotkey as the app keeps it: (key code, modifiers held with it)


class FakeSettingsStore:
    """Stands in for the settings store. It keeps the settings in memory only."""

    def __init__(self, app_settings):
        self.current = app_settings

    def update(self, **new_values):
        self.current = replace(self.current, **new_values)


def make_mirror(name):
    return MirrorSettings(mirror_id=name, name=name, layouts={})


class FakeProfileManager:
    """Stands in for the profile manager. It keeps the mirrors of the open profile."""

    def __init__(self, mirrors):
        self.current = Profile(mirrors=tuple(mirrors))
        self.cleared_hotkeys = []

    def update_mirror(self, mirror_settings):
        mirrors = [
            mirror_settings if kept.mirror_id == mirror_settings.mirror_id else kept
            for kept in self.current.mirrors
        ]
        self.current = Profile(mirrors=tuple(mirrors))

    def remove_mirror(self, mirror_id):
        mirrors = [kept for kept in self.current.mirrors if kept.mirror_id != mirror_id]
        self.current = Profile(mirrors=tuple(mirrors))

    def clear_hotkey(self, key):
        self.cleared_hotkeys.append(key)
        mirrors = [
            replace(kept, timer=replace(kept.timer, key=None)) if kept.timer.key == key else kept
            for kept in self.current.mirrors
        ]
        self.current = Profile(mirrors=tuple(mirrors))


def make_manager(profile_manager, app_settings=DEFAULT_SETTINGS):
    settings_store = FakeSettingsStore(app_settings)
    connection = SimpleNamespace(character=None)
    timer_manager = TimerManager(settings_store, profile_manager, connection)
    return MirrorManager(None, settings_store, profile_manager, timer_manager)


def make_manager_with(names, app_settings=DEFAULT_SETTINGS):
    profile_manager = FakeProfileManager([make_mirror(name) for name in names])
    return make_manager(profile_manager, app_settings)


def make_shown_mirror(name):
    """A mirror with a layout for the size of GAME_WINDOW, so the Mirrors page has a card for it."""
    return replace(make_mirror(name), layouts={"800x600": Layout(Rect(5, 5, 320, 64), (0, 0))})


class FakeMirrorWindow:
    """Stands in for a mirror window. It remembers what it was told and if it was destroyed."""

    def __init__(self, mirror_settings, game_window, mirror_look, on_changed):
        self.name = mirror_settings.name
        self.mirror_settings = mirror_settings
        self.game_window = game_window
        self.mirror_look = mirror_look
        self.on_changed = on_changed
        self.is_destroyed = False

    def set_game_window(self, game_window):
        self.game_window = game_window

    def set_mirror_look(self, mirror_look):
        self.mirror_look = mirror_look

    @property
    def mirror_id(self):
        return self.mirror_settings.mirror_id

    def set_mirror_settings(self, mirror_settings):
        self.mirror_settings = mirror_settings

    def destroy(self):
        self.is_destroyed = True


@pytest.fixture
def screen(monkeypatch):
    """The mirror windows the manager created; a test adds names Windows should refuse."""
    seen = {"created": [], "refused": set()}

    def create_window(parent, mirror_settings, game_window, mirror_look, on_changed):
        if mirror_settings.name in seen["refused"]:
            raise OSError("Windows refused the live picture")
        window = FakeMirrorWindow(mirror_settings, game_window, mirror_look, on_changed)
        seen["created"].append(window)
        return window

    monkeypatch.setattr(mirror_manager_module, "MirrorWindow", create_window)
    return seen


def test_shows_a_window_for_each_mirror(screen):
    manager = make_manager_with(["Minimap", "Health"])

    failed = manager.show(GAME_WINDOW)

    assert failed == 0
    assert [window.name for window in screen["created"]] == ["Minimap", "Health"]


def test_a_refused_mirror_is_left_out_and_counted(screen):
    screen["refused"].add("Health")
    manager = make_manager_with(["Minimap", "Health"])

    failed = manager.show(GAME_WINDOW)

    assert failed == 1
    assert [window.name for window in screen["created"]] == ["Minimap"]


def test_a_refused_mirror_is_still_kept(screen):
    screen["refused"].add("Health")
    manager = make_manager_with(["Minimap", "Health"])
    manager.show(GAME_WINDOW)
    screen["refused"].clear()

    manager.show(GAME_WINDOW)

    assert [window.name for window in screen["created"]][-2:] == ["Minimap", "Health"]


def test_show_closes_the_windows_shown_before(screen):
    manager = make_manager_with(["Minimap"])
    manager.show(GAME_WINDOW)
    old_window = screen["created"][0]

    manager.show(GAME_WINDOW)

    assert old_window.is_destroyed


def test_close_destroys_every_window(screen):
    manager = make_manager_with(["Minimap", "Health"])
    manager.show(GAME_WINDOW)

    manager.close()

    assert all(window.is_destroyed for window in screen["created"])


def test_close_keeps_the_mirrors_for_the_next_show(screen):
    manager = make_manager_with(["Minimap"])
    manager.show(GAME_WINDOW)
    manager.close()

    manager.show(GAME_WINDOW)

    assert [window.name for window in screen["created"]] == ["Minimap", "Minimap"]


def test_set_game_window_moves_every_window(screen):
    manager = make_manager_with(["Minimap", "Health"])
    manager.show(GAME_WINDOW)
    moved = GameWindow(100, Rect(50, 60, 800, 600), is_minimized=False, is_in_front=True)

    manager.set_game_window(moved)

    assert all(window.game_window == moved for window in screen["created"])


def test_new_windows_get_the_look_from_the_settings(screen):
    app_settings = AppSettings(
        is_mirror_frame_on=False,
        is_rounded_corners_on=True,
        is_frame_tint_on=True,
    )
    manager = make_manager_with(["Minimap"], app_settings)

    manager.show(GAME_WINDOW)

    expected_look = MirrorLook(is_frame_on=False, is_rounded_on=True, is_tint_on=True)
    assert screen["created"][0].mirror_look == expected_look


def test_update_mirror_look_reaches_every_window(screen):
    settings_store = SimpleNamespace(current=DEFAULT_SETTINGS)
    profile_manager = FakeProfileManager([make_mirror("Minimap"), make_mirror("Health")])
    manager = MirrorManager(None, settings_store, profile_manager, None)
    manager.show(GAME_WINDOW)
    frameless = MirrorLook(is_frame_on=False, is_rounded_on=False, is_tint_on=False)

    settings_store.current = AppSettings(is_mirror_frame_on=False)
    manager.update_mirror_look()

    assert all(window.mirror_look == frameless for window in screen["created"])


def test_update_windows_gives_a_changed_mirror_its_new_settings(screen):
    profile_manager = FakeProfileManager([make_mirror("Minimap"), make_mirror("Health")])
    manager = make_manager(profile_manager)
    manager.show(GAME_WINDOW)
    changed = replace(make_mirror("Health"), opacity=0.3)
    profile_manager.update_mirror(changed)

    manager.update_windows()

    assert [window.mirror_settings for window in screen["created"]] == [
        make_mirror("Minimap"),
        changed,
    ]


def test_update_windows_closes_only_the_window_of_a_removed_mirror(screen):
    profile_manager = FakeProfileManager([make_mirror("Minimap"), make_mirror("Health")])
    manager = make_manager(profile_manager)
    manager.show(GAME_WINDOW)
    minimap_window, health_window = screen["created"]
    profile_manager.remove_mirror("Health")

    manager.update_windows()

    assert health_window.is_destroyed
    assert not minimap_window.is_destroyed


def test_the_closed_window_of_a_removed_mirror_is_forgotten(screen):
    profile_manager = FakeProfileManager([make_mirror("Minimap"), make_mirror("Health")])
    manager = make_manager(profile_manager)
    manager.show(GAME_WINDOW)
    health_window = screen["created"][1]
    profile_manager.remove_mirror("Health")
    manager.update_windows()
    moved = GameWindow(100, Rect(50, 60, 800, 600), is_minimized=False, is_in_front=True)

    manager.set_game_window(moved)

    assert health_window.game_window == GAME_WINDOW


def test_a_changed_mirror_is_kept_for_the_next_show(screen):
    manager = make_manager_with(["Minimap", "Health"])
    manager.show(GAME_WINDOW)
    changed = replace(make_mirror("Health"), zoom=2.0)

    screen["created"][1].on_changed(changed)
    manager.show(GAME_WINDOW)

    assert [window.mirror_settings for window in screen["created"][-2:]] == [
        make_mirror("Minimap"),
        changed,
    ]


def test_a_changed_mirror_is_passed_on_with_all_mirrors(screen):
    profile_manager = FakeProfileManager([make_mirror("Minimap"), make_mirror("Health")])
    manager = make_manager(profile_manager)
    manager.show(GAME_WINDOW)
    changed = replace(make_mirror("Health"), zoom=2.0)

    screen["created"][1].on_changed(changed)

    assert profile_manager.current.mirrors == (make_mirror("Minimap"), changed)


def test_mirror_infos_have_the_region_for_the_size_of_the_game():
    mirror = replace(
        make_mirror("Cooldowns"),
        layouts={"800x600": Layout(Rect(5, 5, 320, 64), (0, 0))},
        opacity=0.5,
        colour="red",
        is_hidden=True,
        is_locked=True,
        timer=MirrorTimer(is_on=True, alert_seconds=90),
    )
    manager = make_manager(FakeProfileManager([mirror]))

    assert manager.get_mirror_infos(GAME_WINDOW) == [
        MirrorInfo(
            mirror_id="Cooldowns",
            name="Cooldowns",
            area_width=320,
            area_height=64,
            opacity=0.5,
            colour="red",
            is_hidden=True,
            is_locked=True,
            timer=MirrorTimer(is_on=True, alert_seconds=90),
        )
    ]


def test_a_mirror_without_a_layout_for_the_size_of_the_game_gets_no_info():
    other_size = {"1920x1080": Layout(Rect(5, 5, 320, 64), (0, 0))}
    mirror = replace(make_mirror("Cooldowns"), layouts=other_size)
    manager = make_manager(FakeProfileManager([mirror]))

    assert manager.get_mirror_infos(GAME_WINDOW) == []


def test_a_change_from_the_mirrors_page_is_kept_and_passed_on():
    minimap, health = make_shown_mirror("Minimap"), make_shown_mirror("Health")
    profile_manager = FakeProfileManager([minimap, health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos(GAME_WINDOW)[1]

    manager.update_mirror(replace(health_info, is_hidden=True))

    assert profile_manager.current.mirrors == (minimap, replace(health, is_hidden=True))


def test_a_lock_from_the_mirrors_page_is_kept_and_passed_on():
    health = make_shown_mirror("Health")
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos(GAME_WINDOW)[0]

    manager.update_mirror(replace(health_info, is_locked=True))

    assert profile_manager.current.mirrors == (replace(health, is_locked=True),)


def test_a_colour_from_the_mirrors_page_is_kept_and_passed_on():
    health = make_shown_mirror("Health")
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos(GAME_WINDOW)[0]

    manager.update_mirror(replace(health_info, colour="red"))

    assert profile_manager.current.mirrors == (replace(health, colour="red"),)


def test_an_opacity_from_the_mirrors_page_is_kept_and_passed_on():
    health = make_shown_mirror("Health")
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos(GAME_WINDOW)[0]

    manager.update_mirror(replace(health_info, opacity=0.3))

    assert profile_manager.current.mirrors == (replace(health, opacity=0.3),)


def test_a_timer_from_the_mirrors_page_is_kept_and_passed_on():
    health = make_shown_mirror("Health")
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos(GAME_WINDOW)[0]
    timer = MirrorTimer(is_on=True, alert_seconds=90)

    manager.update_mirror(replace(health_info, timer=timer))

    assert profile_manager.current.mirrors == (replace(health, timer=timer),)


def test_a_new_timer_hotkey_is_first_cleared_from_every_place_that_has_it():
    minimap = replace(make_shown_mirror("Minimap"), timer=MirrorTimer(is_on=True, key=F1))
    health = make_shown_mirror("Health")
    profile_manager = FakeProfileManager([minimap, health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos(GAME_WINDOW)[1]
    timer = MirrorTimer(is_on=True, key=F1)

    manager.update_mirror(replace(health_info, timer=timer))

    assert profile_manager.cleared_hotkeys == [F1]
    assert [mirror.timer.key for mirror in profile_manager.current.mirrors] == [None, F1]


def test_a_timer_that_keeps_its_hotkey_clears_nothing():
    health = replace(make_shown_mirror("Health"), timer=MirrorTimer(is_on=True, key=F1))
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos(GAME_WINDOW)[0]

    manager.update_mirror(replace(health_info, opacity=0.3))

    assert profile_manager.cleared_hotkeys == []
    assert profile_manager.current.mirrors == (replace(health, opacity=0.3),)


def test_a_timer_whose_hotkey_is_taken_away_clears_nothing():
    health = replace(make_shown_mirror("Health"), timer=MirrorTimer(is_on=True, key=F1))
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos(GAME_WINDOW)[0]

    manager.update_mirror(replace(health_info, timer=MirrorTimer(is_on=True)))

    assert profile_manager.cleared_hotkeys == []
