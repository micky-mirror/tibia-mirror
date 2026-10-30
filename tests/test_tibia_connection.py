"""The connection to Tibia: what it knows and what it tells the app."""

import pytest

from tibia_mirror.app_parts import tibia_connection as connection_module
from tibia_mirror.app_parts.tibia_connection import TibiaConnection
from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.tibia.connection import CONNECTED, MINIMIZED, WAITING
from tibia_mirror.core.tibia.game_window import GameWindow
from tibia_mirror.winapi import win32

HWND = 100
AREA = Rect(10, 20, 800, 600)
BROWSER = 200


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
    reported = {
        "is_running": True,
        "is_minimized": False,
        "client_area": AREA,
        "front_window": HWND,
        "title": "Tibia",
    }

    def find_window():
        return HWND if reported["is_running"] else None

    monkeypatch.setattr(connection_module, "find_tibia_window", find_window)
    monkeypatch.setattr(win32, "is_window", lambda hwnd: reported["is_running"])
    monkeypatch.setattr(win32, "is_minimized", lambda hwnd: reported["is_minimized"])
    monkeypatch.setattr(win32, "client_rect", lambda hwnd: reported["client_area"])
    monkeypatch.setattr(win32, "foreground_window", lambda: reported["front_window"])
    monkeypatch.setattr(win32, "window_process_id", lambda hwnd: 1)
    monkeypatch.setattr(win32, "window_class", lambda hwnd: "AppWindow")
    monkeypatch.setattr(win32, "window_title", lambda hwnd: reported["title"])
    return reported


def do_nothing(value) -> None:
    pass


def test_state_is_waiting_when_tibia_is_not_running(tibia):
    tibia["is_running"] = False

    connection = TibiaConnection(FakeWindow(), do_nothing, do_nothing, do_nothing)

    assert connection.state == WAITING


def test_state_is_minimized_when_tibia_is_minimized(tibia):
    tibia["is_minimized"] = True

    connection = TibiaConnection(FakeWindow(), do_nothing, do_nothing, do_nothing)

    assert connection.state == MINIMIZED


def test_state_is_connected_when_tibia_is_running(tibia):
    connection = TibiaConnection(FakeWindow(), do_nothing, do_nothing, do_nothing)

    assert connection.state == CONNECTED


def test_game_window_is_known_when_tibia_is_running(tibia):
    connection = TibiaConnection(FakeWindow(), do_nothing, do_nothing, do_nothing)

    assert connection.game_window == GameWindow(HWND, AREA, is_minimized=False, is_in_front=True)


def test_there_is_no_game_window_when_tibia_is_not_running(tibia):
    tibia["is_running"] = False

    connection = TibiaConnection(FakeWindow(), do_nothing, do_nothing, do_nothing)

    assert connection.game_window is None


def test_there_is_no_game_window_when_tibia_was_minimized_from_the_start(tibia):
    tibia["is_minimized"] = True

    connection = TibiaConnection(FakeWindow(), do_nothing, do_nothing, do_nothing)

    assert connection.game_window is None


def test_game_window_is_kept_while_tibia_is_minimized_later(tibia):
    window = FakeWindow()
    connection = TibiaConnection(window, do_nothing, do_nothing, do_nothing)

    tibia["is_minimized"] = True
    window.run_planned()

    assert connection.game_window == GameWindow(HWND, AREA, is_minimized=True, is_in_front=True)


def test_the_logged_in_character_is_read_from_the_title_of_tibia(tibia):
    tibia["title"] = "Tibia - Bubble"

    connection = TibiaConnection(FakeWindow(), do_nothing, do_nothing, do_nothing)

    assert connection.character == "Bubble"


def test_there_is_no_character_on_the_login_screen(tibia):
    connection = TibiaConnection(FakeWindow(), do_nothing, do_nothing, do_nothing)

    assert connection.character is None


def test_there_is_no_character_when_tibia_is_not_running(tibia):
    tibia["is_running"] = False
    tibia["title"] = "Tibia - Bubble"

    connection = TibiaConnection(FakeWindow(), do_nothing, do_nothing, do_nothing)

    assert connection.character is None


def test_nothing_is_told_while_the_state_stays_the_same(tibia):
    window = FakeWindow()
    states = []
    TibiaConnection(window, states.append, do_nothing, do_nothing)

    window.run_planned()

    assert states == []


def test_a_new_state_is_told_to_the_app_one_time(tibia):
    tibia["is_running"] = False
    window = FakeWindow()
    states = []
    TibiaConnection(window, states.append, do_nothing, do_nothing)

    tibia["is_running"] = True
    window.run_planned()
    window.run_planned()

    assert states == [CONNECTED]


def test_a_restored_tibia_is_connected(tibia):
    tibia["is_minimized"] = True
    window = FakeWindow()
    states = []
    TibiaConnection(window, states.append, do_nothing, do_nothing)

    tibia["is_minimized"] = False
    window.run_planned()

    assert states == [CONNECTED]


def test_state_is_waiting_again_after_tibia_closes(tibia):
    window = FakeWindow()
    states = []
    connection = TibiaConnection(window, states.append, do_nothing, do_nothing)

    tibia["is_running"] = False
    window.run_planned()

    assert connection.state == WAITING
    assert states == [WAITING]


def test_checks_go_on_after_an_error_in_one_check(tibia):
    def fail(state):
        raise RuntimeError("the app failed to show the state")

    tibia["is_running"] = False
    window = FakeWindow()
    TibiaConnection(window, fail, do_nothing, do_nothing)

    tibia["is_running"] = True
    with pytest.raises(RuntimeError):
        window.run_planned()

    assert window.planned is not None


def test_a_moved_tibia_is_told_to_the_app(tibia):
    window = FakeWindow()
    game_windows = []
    TibiaConnection(window, do_nothing, game_windows.append, do_nothing)

    tibia["client_area"] = Rect(50, 60, 800, 600)
    window.run_planned()

    assert game_windows == [
        GameWindow(HWND, Rect(50, 60, 800, 600), is_minimized=False, is_in_front=True)
    ]


def test_nothing_is_told_while_tibia_stays_in_place(tibia):
    window = FakeWindow()
    game_windows = []
    TibiaConnection(window, do_nothing, game_windows.append, do_nothing)

    window.run_planned()

    assert game_windows == []


def test_a_new_connection_is_told_only_as_a_new_state(tibia):
    tibia["is_running"] = False
    window = FakeWindow()
    game_windows = []
    TibiaConnection(window, do_nothing, game_windows.append, do_nothing)

    tibia["is_running"] = True
    window.run_planned()

    assert game_windows == []


def test_a_minimized_tibia_is_told_as_a_new_game_window(tibia):
    window = FakeWindow()
    game_windows = []
    TibiaConnection(window, do_nothing, game_windows.append, do_nothing)

    tibia["is_minimized"] = True
    window.run_planned()

    assert game_windows == [GameWindow(HWND, AREA, is_minimized=True, is_in_front=True)]


def test_a_restored_tibia_is_told_as_a_new_game_window(tibia):
    window = FakeWindow()
    game_windows = []
    TibiaConnection(window, do_nothing, game_windows.append, do_nothing)

    tibia["is_minimized"] = True
    window.run_planned()
    tibia["is_minimized"] = False
    window.run_planned()

    assert game_windows[-1] == GameWindow(HWND, AREA, is_minimized=False, is_in_front=True)


def test_another_window_in_front_is_told_as_a_new_game_window(tibia):
    window = FakeWindow()
    game_windows = []
    TibiaConnection(window, do_nothing, game_windows.append, do_nothing)

    tibia["front_window"] = BROWSER
    window.run_planned()

    assert game_windows == [GameWindow(HWND, AREA, is_minimized=False, is_in_front=False)]


def test_tibia_back_in_front_is_told_as_a_new_game_window(tibia):
    window = FakeWindow()
    game_windows = []
    TibiaConnection(window, do_nothing, game_windows.append, do_nothing)

    tibia["front_window"] = BROWSER
    window.run_planned()
    tibia["front_window"] = HWND
    window.run_planned()

    assert game_windows[-1] == GameWindow(HWND, AREA, is_minimized=False, is_in_front=True)


def test_a_login_is_told_to_the_app(tibia):
    window = FakeWindow()
    characters = []
    TibiaConnection(window, do_nothing, do_nothing, characters.append)

    tibia["title"] = "Tibia - Bubble"
    window.run_planned()

    assert characters == ["Bubble"]


def test_a_logout_is_told_to_the_app(tibia):
    tibia["title"] = "Tibia - Bubble"
    window = FakeWindow()
    characters = []
    TibiaConnection(window, do_nothing, do_nothing, characters.append)

    tibia["title"] = "Tibia"
    window.run_planned()

    assert characters == [None]


def test_nothing_is_told_while_the_same_character_stays_logged_in(tibia):
    tibia["title"] = "Tibia - Bubble"
    window = FakeWindow()
    characters = []
    TibiaConnection(window, do_nothing, do_nothing, characters.append)

    window.run_planned()

    assert characters == []
