"""The connection to Tibia: what it knows and what it tells the app."""

import pytest

from tibia_mirror.app_parts.tibia_connection import TibiaConnection
from tibia_mirror.core.connection import CONNECTED, MINIMIZED, WAITING
from tibia_mirror.core.geometry import Rect
from tibia_mirror.services import game as game_module
from tibia_mirror.winapi import win32

HWND = 100
AREA = Rect(10, 20, 800, 600)


class FakeWindow:
    """Stands in for the app window. It only remembers the function that was planned."""

    def __init__(self) -> None:
        self.planned = None  # the function given to after()

    def after(self, delay_ms, function):
        self.planned = function


@pytest.fixture
def tibia(monkeypatch):
    """What Windows reports about Tibia; a test changes it to set the scene."""
    reported = {"is_running": True, "is_minimized": False}

    def find_window():
        return HWND if reported["is_running"] else None

    monkeypatch.setattr(game_module, "find_tibia_window", find_window)
    monkeypatch.setattr(win32, "is_window", lambda hwnd: reported["is_running"])
    monkeypatch.setattr(win32, "is_minimized", lambda hwnd: reported["is_minimized"])
    monkeypatch.setattr(win32, "client_rect", lambda hwnd: AREA)
    return reported


def do_nothing(state: str) -> None:
    pass


def test_state_is_waiting_when_tibia_is_not_running(tibia):
    tibia["is_running"] = False

    connection = TibiaConnection(FakeWindow(), do_nothing)

    assert connection.state == WAITING


def test_state_is_minimized_when_tibia_is_minimized(tibia):
    tibia["is_minimized"] = True

    connection = TibiaConnection(FakeWindow(), do_nothing)

    assert connection.state == MINIMIZED


def test_state_is_connected_when_tibia_is_running(tibia):
    connection = TibiaConnection(FakeWindow(), do_nothing)

    assert connection.state == CONNECTED
