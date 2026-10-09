import pytest

from tibia_mirror.core.geometry import Rect
from tibia_mirror.services import game as game_module
from tibia_mirror.services.game import Game
from tibia_mirror.winapi import win32

HWND = 100
AREA = Rect(10, 20, 800, 600)


@pytest.fixture
def window(monkeypatch):
    """What Windows reports about the Tibia window; a test changes it to set the scene."""
    reported = {"minimized": False, "client": AREA}
    monkeypatch.setattr(win32, "is_minimized", lambda hwnd: reported["minimized"])
    monkeypatch.setattr(win32, "client_rect", lambda hwnd: reported["client"])
    return reported


@pytest.fixture
def game(window):
    game = Game()
    game.hwnd = HWND
    return game


def test_no_client_area_before_tibia_is_found(window):
    assert Game().read_client() is None


def test_reads_the_client_area_of_the_window(game):
    assert game.read_client() == AREA


def test_a_minimized_window_has_no_client_area(game, window):
    window["minimized"] = True
    assert game.read_client() is None


def test_an_empty_client_area_counts_as_none(game, window):
    window["client"] = Rect(10, 20, 0, 0)
    assert game.read_client() is None


def test_current_client_follows_the_window(game, window):
    assert game.current_client() == AREA
    moved = Rect(50, 60, 800, 600)
    window["client"] = moved
    assert game.current_client() == moved
    assert game.client == moved


def test_current_client_remembers_the_area_while_minimized(game, window):
    game.current_client()
    window["minimized"] = True
    assert game.read_client() is None
    assert game.current_client() == AREA


def test_find_looks_for_tibia_until_it_is_running(monkeypatch):
    running = {"hwnd": None}
    monkeypatch.setattr(game_module, "find_tibia_window", lambda: running["hwnd"])
    game = Game()
    assert game.find() is None
    running["hwnd"] = HWND
    assert game.find() == HWND
    assert game.hwnd == HWND


def test_find_keeps_the_window_it_already_has(game, monkeypatch):
    def search_again():
        raise AssertionError("searched although the window is known")

    monkeypatch.setattr(game_module, "find_tibia_window", search_again)
    assert game.find() == HWND


def test_check_closed_is_false_before_tibia_is_found():
    assert not Game().check_closed()


def test_check_closed_is_false_while_tibia_runs(game, monkeypatch):
    monkeypatch.setattr(win32, "is_window", lambda hwnd: True)
    assert not game.check_closed()
    assert game.hwnd == HWND


def test_check_closed_forgets_a_window_that_is_gone(game, monkeypatch):
    game.current_client()
    monkeypatch.setattr(win32, "is_window", lambda hwnd: False)
    assert game.check_closed()
    assert game.hwnd is None
    assert game.client is None
    assert not game.check_closed()
