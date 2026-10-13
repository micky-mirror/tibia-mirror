"""The connection to Tibia: what it knows and what it tells the app."""

import pytest

from tibia_mirror.app_parts.tibia_connection import TibiaConnection
from tibia_mirror.core.connection import CONNECTED, MINIMIZED, WAITING
from tibia_mirror.core.game_window import GameWindow
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

    def run_planned(self) -> None:
        """Run the planned function, as the real window does when the wait is over."""
        function = self.planned
        self.planned = None
        function()


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


def test_game_window_is_known_when_tibia_is_running(tibia):
    connection = TibiaConnection(FakeWindow(), do_nothing)

    assert connection.game_window == GameWindow(HWND, AREA)


def test_there_is_no_game_window_when_tibia_is_not_running(tibia):
    tibia["is_running"] = False

    connection = TibiaConnection(FakeWindow(), do_nothing)

    assert connection.game_window is None


def test_there_is_no_game_window_when_tibia_was_minimized_from_the_start(tibia):
    tibia["is_minimized"] = True

    connection = TibiaConnection(FakeWindow(), do_nothing)

    assert connection.game_window is None


def test_game_window_is_kept_while_tibia_is_minimized_later(tibia):
    window = FakeWindow()
    connection = TibiaConnection(window, do_nothing)

    tibia["is_minimized"] = True
    window.run_planned()

    assert connection.game_window == GameWindow(HWND, AREA)


def test_nothing_is_told_while_the_state_stays_the_same(tibia):
    window = FakeWindow()
    states = []
    TibiaConnection(window, states.append)

    window.run_planned()

    assert states == []


def test_a_new_state_is_told_to_the_app_one_time(tibia):
    tibia["is_running"] = False
    window = FakeWindow()
    states = []
    TibiaConnection(window, states.append)

    tibia["is_running"] = True
    window.run_planned()
    window.run_planned()

    assert states == [CONNECTED]


def test_a_restored_tibia_is_connected(tibia):
    tibia["is_minimized"] = True
    window = FakeWindow()
    states = []
    TibiaConnection(window, states.append)

    tibia["is_minimized"] = False
    window.run_planned()

    assert states == [CONNECTED]


def test_state_is_waiting_again_after_tibia_closes(tibia):
    window = FakeWindow()
    states = []
    connection = TibiaConnection(window, states.append)

    tibia["is_running"] = False
    window.run_planned()

    assert connection.state == WAITING
    assert states == [WAITING]


def test_checks_go_on_after_an_error_in_one_check(tibia):
    def fail(state):
        raise RuntimeError("the app failed to show the state")

    tibia["is_running"] = False
    window = FakeWindow()
    TibiaConnection(window, fail)

    tibia["is_running"] = True
    with pytest.raises(RuntimeError):
        window.run_planned()

    assert window.planned is not None
