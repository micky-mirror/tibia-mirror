"""The mirror manager: which mirror windows it shows and closes."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from tibia_mirror.app_parts import mirror_manager as mirror_manager_module
from tibia_mirror.app_parts.mirror_manager import MirrorManager
from tibia_mirror.app_parts.timer_manager import TimerManager
from tibia_mirror.config import FRAME_COLORS, NEW_MIRROR_GAP
from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.mirror_look import MirrorLook
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.mirror_timer import MirrorTimer
from tibia_mirror.core.profile import Profile
from tibia_mirror.core.regions import Layout
from tibia_mirror.core.tibia.game_window import GameWindow
from tibia_mirror.settings.app_settings import AppSettings
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.mirrors.mirror_info import MirrorInfo
from tibia_mirror.winapi import win32

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

    def add_mirror(self, mirror_settings):
        self.current = Profile(mirrors=(*self.current.mirrors, mirror_settings))

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


def make_manager(profile_manager, app_settings=DEFAULT_SETTINGS, game_window=GAME_WINDOW):
    """A mirror manager for this window of Tibia. None: Tibia is not connected."""
    settings_store = FakeSettingsStore(app_settings)
    connection = SimpleNamespace(character=None, game_window=game_window)
    timer_manager = TimerManager(settings_store, profile_manager, connection)
    return MirrorManager(None, settings_store, profile_manager, timer_manager, connection)


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

    failed = manager.show()

    assert failed == 0
    assert [window.name for window in screen["created"]] == ["Minimap", "Health"]


def test_a_refused_mirror_is_left_out_and_counted(screen):
    screen["refused"].add("Health")
    manager = make_manager_with(["Minimap", "Health"])

    failed = manager.show()

    assert failed == 1
    assert [window.name for window in screen["created"]] == ["Minimap"]


def test_a_refused_mirror_is_still_kept(screen):
    screen["refused"].add("Health")
    manager = make_manager_with(["Minimap", "Health"])
    manager.show()
    screen["refused"].clear()

    manager.show()

    assert [window.name for window in screen["created"]][-2:] == ["Minimap", "Health"]


def test_show_closes_the_windows_shown_before(screen):
    manager = make_manager_with(["Minimap"])
    manager.show()
    old_window = screen["created"][0]

    manager.show()

    assert old_window.is_destroyed


def test_close_destroys_every_window(screen):
    manager = make_manager_with(["Minimap", "Health"])
    manager.show()

    manager.close()

    assert all(window.is_destroyed for window in screen["created"])


def test_close_keeps_the_mirrors_for_the_next_show(screen):
    manager = make_manager_with(["Minimap"])
    manager.show()
    manager.close()

    manager.show()

    assert [window.name for window in screen["created"]] == ["Minimap", "Minimap"]


def test_set_game_window_moves_every_window(screen):
    manager = make_manager_with(["Minimap", "Health"])
    manager.show()
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

    manager.show()

    expected_look = MirrorLook(is_frame_on=False, is_rounded_on=True, is_tint_on=True)
    assert screen["created"][0].mirror_look == expected_look


def test_update_mirror_look_reaches_every_window(screen):
    settings_store = SimpleNamespace(current=DEFAULT_SETTINGS)
    profile_manager = FakeProfileManager([make_mirror("Minimap"), make_mirror("Health")])
    connection = SimpleNamespace(game_window=GAME_WINDOW)
    manager = MirrorManager(None, settings_store, profile_manager, None, connection)
    manager.show()
    frameless = MirrorLook(is_frame_on=False, is_rounded_on=False, is_tint_on=False)

    settings_store.current = AppSettings(is_mirror_frame_on=False)
    manager.update_mirror_look()

    assert all(window.mirror_look == frameless for window in screen["created"])


def test_update_windows_gives_a_changed_mirror_its_new_settings(screen):
    profile_manager = FakeProfileManager([make_mirror("Minimap"), make_mirror("Health")])
    manager = make_manager(profile_manager)
    manager.show()
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
    manager.show()
    minimap_window, health_window = screen["created"]
    profile_manager.remove_mirror("Health")

    manager.update_windows()

    assert health_window.is_destroyed
    assert not minimap_window.is_destroyed


def test_the_closed_window_of_a_removed_mirror_is_forgotten(screen):
    profile_manager = FakeProfileManager([make_mirror("Minimap"), make_mirror("Health")])
    manager = make_manager(profile_manager)
    manager.show()
    health_window = screen["created"][1]
    profile_manager.remove_mirror("Health")
    manager.update_windows()
    moved = GameWindow(100, Rect(50, 60, 800, 600), is_minimized=False, is_in_front=True)

    manager.set_game_window(moved)

    assert health_window.game_window == GAME_WINDOW


def test_a_changed_mirror_is_kept_for_the_next_show(screen):
    manager = make_manager_with(["Minimap", "Health"])
    manager.show()
    changed = replace(make_mirror("Health"), zoom=2.0)

    screen["created"][1].on_changed(changed)
    manager.show()

    assert [window.mirror_settings for window in screen["created"][-2:]] == [
        make_mirror("Minimap"),
        changed,
    ]


def test_a_changed_mirror_is_passed_on_with_all_mirrors(screen):
    profile_manager = FakeProfileManager([make_mirror("Minimap"), make_mirror("Health")])
    manager = make_manager(profile_manager)
    manager.show()
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

    assert manager.get_mirror_infos() == [
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

    assert manager.get_mirror_infos() == []


def test_a_change_from_the_mirrors_page_is_kept_and_passed_on():
    minimap, health = make_shown_mirror("Minimap"), make_shown_mirror("Health")
    profile_manager = FakeProfileManager([minimap, health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos()[1]

    manager.update_mirror(replace(health_info, is_hidden=True))

    assert profile_manager.current.mirrors == (minimap, replace(health, is_hidden=True))


def test_a_lock_from_the_mirrors_page_is_kept_and_passed_on():
    health = make_shown_mirror("Health")
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos()[0]

    manager.update_mirror(replace(health_info, is_locked=True))

    assert profile_manager.current.mirrors == (replace(health, is_locked=True),)


def test_a_colour_from_the_mirrors_page_is_kept_and_passed_on():
    health = make_shown_mirror("Health")
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos()[0]

    manager.update_mirror(replace(health_info, colour="red"))

    assert profile_manager.current.mirrors == (replace(health, colour="red"),)


def test_a_name_from_the_mirrors_page_is_kept_and_passed_on():
    health = make_shown_mirror("Health")
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos()[0]

    manager.update_mirror(replace(health_info, name="Life"))

    assert profile_manager.current.mirrors == (replace(health, name="Life"),)


def test_an_opacity_from_the_mirrors_page_is_kept_and_passed_on():
    health = make_shown_mirror("Health")
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos()[0]

    manager.update_mirror(replace(health_info, opacity=0.3))

    assert profile_manager.current.mirrors == (replace(health, opacity=0.3),)


def test_a_timer_from_the_mirrors_page_is_kept_and_passed_on():
    health = make_shown_mirror("Health")
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos()[0]
    timer = MirrorTimer(is_on=True, alert_seconds=90)

    manager.update_mirror(replace(health_info, timer=timer))

    assert profile_manager.current.mirrors == (replace(health, timer=timer),)


def test_a_new_timer_hotkey_is_first_cleared_from_every_place_that_has_it():
    minimap = replace(make_shown_mirror("Minimap"), timer=MirrorTimer(is_on=True, key=F1))
    health = make_shown_mirror("Health")
    profile_manager = FakeProfileManager([minimap, health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos()[1]
    timer = MirrorTimer(is_on=True, key=F1)

    manager.update_mirror(replace(health_info, timer=timer))

    assert profile_manager.cleared_hotkeys == [F1]
    assert [mirror.timer.key for mirror in profile_manager.current.mirrors] == [None, F1]


def test_a_timer_that_keeps_its_hotkey_clears_nothing():
    health = replace(make_shown_mirror("Health"), timer=MirrorTimer(is_on=True, key=F1))
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos()[0]

    manager.update_mirror(replace(health_info, opacity=0.3))

    assert profile_manager.cleared_hotkeys == []
    assert profile_manager.current.mirrors == (replace(health, opacity=0.3),)


def test_a_timer_whose_hotkey_is_taken_away_clears_nothing():
    health = replace(make_shown_mirror("Health"), timer=MirrorTimer(is_on=True, key=F1))
    profile_manager = FakeProfileManager([health])
    manager = make_manager(profile_manager)
    health_info = manager.get_mirror_infos()[0]

    manager.update_mirror(replace(health_info, timer=MirrorTimer(is_on=True)))

    assert profile_manager.cleared_hotkeys == []


def use_work_area(monkeypatch, work_area):
    """Make `work_area` the screen without the taskbar, wherever the mirror goes."""
    monkeypatch.setattr(win32, "work_area_at", lambda point: work_area)


def add_mirror(area, app_settings=DEFAULT_SETTINGS):
    """Add one mirror of `area` on GAME_WINDOW, and return its settings."""
    profile_manager = FakeProfileManager([])
    manager = make_manager(profile_manager, app_settings)

    manager.add_mirror("Region 1", area)

    (added,) = profile_manager.current.mirrors
    return added


def test_an_added_mirror_shows_its_area_at_zoom_one_with_the_new_mirror_opacity(monkeypatch):
    use_work_area(monkeypatch, Rect(0, 0, 1920, 1040))
    area = Rect(30, 40, 200, 100)

    added = add_mirror(area, replace(DEFAULT_SETTINGS, new_mirror_opacity=0.5))

    assert added.name == "Region 1"
    assert added.layouts["800x600"].region == area
    assert added.zoom == 1.0
    assert added.opacity == 0.5


def test_an_added_mirror_sits_right_of_its_area(monkeypatch):
    use_work_area(monkeypatch, Rect(0, 0, 1920, 1040))

    added = add_mirror(Rect(30, 40, 200, 100))

    # On the screen the area starts at (40, 60), because the game starts at (10, 20).
    # The offset is counted from the start of the game.
    gap = px(NEW_MIRROR_GAP)
    assert added.layouts["800x600"].offset == (30 + 200 + gap, 40)


def test_an_added_mirror_sits_left_of_its_area_when_the_right_has_no_room(monkeypatch):
    use_work_area(monkeypatch, Rect(0, 0, 1000, 1040))

    added = add_mirror(Rect(600, 40, 190, 100))

    # The area ends at 800 on the screen, so the mirror would end past 1000 on the right.
    gap = px(NEW_MIRROR_GAP)
    assert added.layouts["800x600"].offset == (600 - gap - 190, 40)


def test_every_added_mirror_gets_its_own_id(monkeypatch):
    use_work_area(monkeypatch, Rect(0, 0, 1920, 1040))
    profile_manager = FakeProfileManager([])
    manager = make_manager(profile_manager)
    area = Rect(30, 40, 200, 100)

    manager.add_mirror("Region 1", area)
    manager.add_mirror("Region 2", area)

    first, second = profile_manager.current.mirrors
    assert first.mirror_id != second.mirror_id


def test_an_area_selected_again_replaces_the_area_and_keeps_the_place():
    mirror = replace(
        make_shown_mirror("Minimap"),
        colour=FRAME_COLORS[2],
        layouts={"800x600": Layout(Rect(5, 5, 320, 64), (7, 8))},
    )
    profile_manager = FakeProfileManager([mirror])
    manager = make_manager(profile_manager)

    manager.set_area("Minimap", Rect(10, 20, 100, 50))

    (changed,) = profile_manager.current.mirrors
    assert changed.layouts == {"800x600": Layout(Rect(10, 20, 100, 50), (7, 8))}
    assert changed.colour == FRAME_COLORS[2]


def test_an_area_selected_again_keeps_the_areas_for_other_game_sizes():
    big_game_layout = Layout(Rect(50, 50, 640, 128), (0, 0))
    mirror = replace(
        make_shown_mirror("Minimap"),
        layouts={"800x600": Layout(Rect(5, 5, 320, 64), (7, 8)), "1920x1080": big_game_layout},
    )
    profile_manager = FakeProfileManager([mirror])
    manager = make_manager(profile_manager)

    manager.set_area("Minimap", Rect(10, 20, 100, 50))

    (changed,) = profile_manager.current.mirrors
    assert changed.layouts["1920x1080"] == big_game_layout


def test_a_mirror_without_a_place_for_this_game_size_goes_beside_its_new_area(monkeypatch):
    use_work_area(monkeypatch, Rect(0, 0, 1920, 1040))
    profile_manager = FakeProfileManager([make_mirror("Minimap")])
    manager = make_manager(profile_manager)

    manager.set_area("Minimap", Rect(30, 40, 200, 100))

    (changed,) = profile_manager.current.mirrors
    gap = px(NEW_MIRROR_GAP)
    assert changed.layouts["800x600"] == Layout(Rect(30, 40, 200, 100), (30 + 200 + gap, 40))


def test_an_area_for_an_unknown_mirror_changes_nothing():
    mirror = make_shown_mirror("Minimap")
    profile_manager = FakeProfileManager([mirror])
    manager = make_manager(profile_manager)

    manager.set_area("Health", Rect(10, 20, 100, 50))

    assert profile_manager.current.mirrors == (mirror,)


def test_no_window_shows_without_tibia(screen):
    profile_manager = FakeProfileManager([make_shown_mirror("Minimap")])
    manager = make_manager(profile_manager, game_window=None)

    failed = manager.show()

    assert failed == 0
    assert screen["created"] == []


def test_the_mirrors_page_gets_no_infos_without_tibia():
    profile_manager = FakeProfileManager([make_shown_mirror("Minimap")])
    manager = make_manager(profile_manager, game_window=None)

    assert manager.get_mirror_infos() is None


def test_no_mirror_is_added_without_tibia():
    profile_manager = FakeProfileManager([])
    manager = make_manager(profile_manager, game_window=None)

    manager.add_mirror("Region 1", Rect(30, 40, 200, 100))

    assert profile_manager.current.mirrors == ()


def test_no_area_is_selected_again_without_tibia():
    mirror = make_shown_mirror("Minimap")
    profile_manager = FakeProfileManager([mirror])
    manager = make_manager(profile_manager, game_window=None)

    manager.set_area("Minimap", Rect(10, 20, 100, 50))

    assert profile_manager.current.mirrors == (mirror,)
