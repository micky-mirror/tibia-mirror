"""The connection to Tibia."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.app_parts.front_window_tracker import FrontWindowTracker
from tibia_mirror.config import CONNECTION_POLL_MS
from tibia_mirror.core import characters
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.services.game import Game


class TibiaConnection:
    """Knows if Tibia is running, if its window can be seen, and who is logged in."""

    def __init__(
        self,
        window: tk.Misc,
        on_state_changed: Callable[[str], None],
        on_game_window_changed: Callable[[GameWindow], None],
        on_character_changed: Callable[[str | None], None],
    ) -> None:
        self._window = window
        # Called with the new state every time the state changes.
        self._on_state_changed = on_state_changed
        self._on_game_window_changed = on_game_window_changed
        self._on_character_changed = on_character_changed
        self._game = Game()
        self._front_window_tracker = FrontWindowTracker()
        self._is_minimized = False
        self._character: str | None = None
        self._look_for_tibia()
        self._check_on_delay()

    @property
    def state(self) -> str:
        """The state of the connection: WAITING, MINIMIZED or CONNECTED."""
        return self._game.state

    @property
    def game_window(self) -> GameWindow | None:
        """The window of Tibia. None while the state is not CONNECTED."""
        handle = self._game.hwnd
        client_area = self._game.client

        if handle is None or client_area is None:
            return None

        is_in_front = self._front_window_tracker.last_front_window == handle

        return GameWindow(handle, client_area, self._is_minimized, is_in_front)

    @property
    def character(self) -> str | None:
        """The character logged in to Tibia. None on the login screen and without Tibia."""
        return self._character

    def _look_for_tibia(self) -> None:
        """Read what is true about Tibia now."""
        self._game.check_closed()
        self._game.find()
        self._game.current_client()
        self._is_minimized = self._game.is_minimized()
        self._character = characters.character_in_title(self._game.title())
        self._front_window_tracker.update()

    def _check_on_delay(self) -> None:
        """Plan the next check."""
        self._window.after(CONNECTION_POLL_MS, self._check)

    def _check(self) -> None:
        """Look for Tibia again, and tell the app what changed."""
        # plan the next check first, so an error in this one cannot stop the checks
        self._check_on_delay()

        previous_state = self.state
        previous_game_window = self.game_window
        previous_character = self._character
        self._look_for_tibia()
        game_window = self.game_window

        if self.state != previous_state:
            self._on_state_changed(self.state)
        elif game_window is not None and game_window != previous_game_window:
            self._on_game_window_changed(game_window)

        if self._character != previous_character:
            self._on_character_changed(self._character)
