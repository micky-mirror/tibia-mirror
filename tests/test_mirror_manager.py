"""The mirror manager: which mirror windows it shows and closes."""

import pytest

from tibia_mirror.app_parts import mirror_manager as mirror_manager_module
from tibia_mirror.app_parts.mirror_manager import MirrorManager
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.mirror_settings import MirrorSettings

GAME_WINDOW = GameWindow(100, Rect(10, 20, 800, 600), is_minimized=False, is_in_front=True)


def make_mirror(name):
    return MirrorSettings(mirror_id=name, name=name, layouts={})


class FakeMirrorWindow:
    """Stands in for a mirror window. It remembers what it was told and if it was destroyed."""

    def __init__(self, name, game_window, is_visible):
        self.name = name
        self.game_window = game_window
        self.is_visible = is_visible
        self.is_destroyed = False

    def set_game_window(self, game_window):
        self.game_window = game_window

    def set_visible(self, is_visible):
        self.is_visible = is_visible

    def destroy(self):
        self.is_destroyed = True


@pytest.fixture
def screen(monkeypatch):
    """The mirror windows the manager created; a test adds names Windows should refuse."""
    seen = {"created": [], "refused": set()}

    def create_window(parent, mirror_settings, game_window, is_visible):
        if mirror_settings.name in seen["refused"]:
            raise OSError("Windows refused the live picture")
        window = FakeMirrorWindow(mirror_settings.name, game_window, is_visible)
        seen["created"].append(window)
        return window

    monkeypatch.setattr(mirror_manager_module, "MirrorWindow", create_window)
    return seen


def test_shows_a_window_for_each_mirror(screen):
    manager = MirrorManager(None, None)

    failed = manager.show([make_mirror("Minimap"), make_mirror("Health")], GAME_WINDOW)

    assert failed == 0
    assert [window.name for window in screen["created"]] == ["Minimap", "Health"]


def test_a_refused_mirror_is_left_out_and_counted(screen):
    screen["refused"].add("Health")
    manager = MirrorManager(None, None)

    failed = manager.show([make_mirror("Minimap"), make_mirror("Health")], GAME_WINDOW)

    assert failed == 1
    assert [window.name for window in screen["created"]] == ["Minimap"]


def test_show_closes_the_windows_shown_before(screen):
    manager = MirrorManager(None, None)
    manager.show([make_mirror("Minimap")], GAME_WINDOW)
    old_window = screen["created"][0]

    manager.show([make_mirror("Health")], GAME_WINDOW)

    assert old_window.is_destroyed


def test_close_destroys_every_window(screen):
    manager = MirrorManager(None, None)
    manager.show([make_mirror("Minimap"), make_mirror("Health")], GAME_WINDOW)

    manager.close()

    assert all(window.is_destroyed for window in screen["created"])


def test_set_game_window_moves_every_window(screen):
    manager = MirrorManager(None, None)
    manager.show([make_mirror("Minimap"), make_mirror("Health")], GAME_WINDOW)
    moved = GameWindow(100, Rect(50, 60, 800, 600), is_minimized=False, is_in_front=True)

    manager.set_game_window(moved)

    assert all(window.game_window == moved for window in screen["created"])


def test_set_visible_reaches_every_window(screen):
    manager = MirrorManager(None, None)
    manager.show([make_mirror("Minimap"), make_mirror("Health")], GAME_WINDOW)

    manager.set_visible(False)

    assert not any(window.is_visible for window in screen["created"])


def test_new_windows_get_the_last_visibility(screen):
    manager = MirrorManager(None, None)
    manager.set_visible(False)

    manager.show([make_mirror("Minimap")], GAME_WINDOW)

    assert not screen["created"][0].is_visible
