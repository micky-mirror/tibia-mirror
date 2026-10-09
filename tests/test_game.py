import pytest

from tibia_mirror.core.geometry import Rect
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
