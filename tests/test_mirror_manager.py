"""The mirror manager: which mirror windows it shows and closes."""

from types import SimpleNamespace

import pytest

from tibia_mirror.app_parts import mirror_manager as mirror_manager_module
from tibia_mirror.app_parts.mirror_manager import MirrorManager
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.mirror_look import MirrorLook
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.settings.app_settings import AppSettings

GAME_WINDOW = GameWindow(100, Rect(10, 20, 800, 600), is_minimized=False, is_in_front=True)
DEFAULT_SETTINGS = AppSettings()


def make_mirror(name):
    return MirrorSettings(mirror_id=name, name=name, layouts={})


def make_manager(app_settings=DEFAULT_SETTINGS):
    settings_store = SimpleNamespace(current=app_settings)
    return MirrorManager(None, settings_store)


class FakeMirrorWindow:
    """Stands in for a mirror window. It remembers what it was told and if it was destroyed."""

    def __init__(self, name, game_window, mirror_look):
        self.name = name
        self.game_window = game_window
        self.mirror_look = mirror_look
        self.is_destroyed = False

    def set_game_window(self, game_window):
        self.game_window = game_window

    def set_mirror_look(self, mirror_look):
        self.mirror_look = mirror_look

    def destroy(self):
        self.is_destroyed = True


@pytest.fixture
def screen(monkeypatch):
    """The mirror windows the manager created; a test adds names Windows should refuse."""
    seen = {"created": [], "refused": set()}

    def create_window(parent, mirror_settings, game_window, mirror_look):
        if mirror_settings.name in seen["refused"]:
            raise OSError("Windows refused the live picture")
        window = FakeMirrorWindow(mirror_settings.name, game_window, mirror_look)
        seen["created"].append(window)
        return window

    monkeypatch.setattr(mirror_manager_module, "MirrorWindow", create_window)
    return seen


def test_shows_a_window_for_each_mirror(screen):
    manager = make_manager()

    failed = manager.show([make_mirror("Minimap"), make_mirror("Health")], GAME_WINDOW)

    assert failed == 0
    assert [window.name for window in screen["created"]] == ["Minimap", "Health"]


def test_a_refused_mirror_is_left_out_and_counted(screen):
    screen["refused"].add("Health")
    manager = make_manager()

    failed = manager.show([make_mirror("Minimap"), make_mirror("Health")], GAME_WINDOW)

    assert failed == 1
    assert [window.name for window in screen["created"]] == ["Minimap"]


def test_show_closes_the_windows_shown_before(screen):
    manager = make_manager()
    manager.show([make_mirror("Minimap")], GAME_WINDOW)
    old_window = screen["created"][0]

    manager.show([make_mirror("Health")], GAME_WINDOW)

    assert old_window.is_destroyed


def test_close_destroys_every_window(screen):
    manager = make_manager()
    manager.show([make_mirror("Minimap"), make_mirror("Health")], GAME_WINDOW)

    manager.close()

    assert all(window.is_destroyed for window in screen["created"])


def test_set_game_window_moves_every_window(screen):
    manager = make_manager()
    manager.show([make_mirror("Minimap"), make_mirror("Health")], GAME_WINDOW)
    moved = GameWindow(100, Rect(50, 60, 800, 600), is_minimized=False, is_in_front=True)

    manager.set_game_window(moved)

    assert all(window.game_window == moved for window in screen["created"])


def test_new_windows_get_the_look_from_the_settings(screen):
    app_settings = AppSettings(
        is_mirror_frame_on=False,
        is_rounded_corners_on=True,
        is_frame_tint_on=True,
    )
    manager = make_manager(app_settings)

    manager.show([make_mirror("Minimap")], GAME_WINDOW)

    expected_look = MirrorLook(is_frame_on=False, is_rounded_on=True, is_tint_on=True)
    assert screen["created"][0].mirror_look == expected_look


def test_update_mirror_look_reaches_every_window(screen):
    settings_store = SimpleNamespace(current=DEFAULT_SETTINGS)
    manager = MirrorManager(None, settings_store)
    manager.show([make_mirror("Minimap"), make_mirror("Health")], GAME_WINDOW)
    frameless = MirrorLook(is_frame_on=False, is_rounded_on=False, is_tint_on=False)

    settings_store.current = AppSettings(is_mirror_frame_on=False)
    manager.update_mirror_look()

    assert all(window.mirror_look == frameless for window in screen["created"])
