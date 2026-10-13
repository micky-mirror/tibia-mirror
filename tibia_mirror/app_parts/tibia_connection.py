"""The connection to Tibia."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.config import ATTACH_POLL_MS
from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.services.game import Game


class TibiaConnection:
    """Knows if Tibia is running and if its window can be seen."""

    def __init__(self, window: tk.Misc, on_state_changed: Callable[[str], None]) -> None:
        self._window = window
        # Called with the new state every time the state changes.
        self._on_state_changed = on_state_changed
        self._game = Game()
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

        return GameWindow(handle, client_area)

    def _look_for_tibia(self) -> None:
        """Read what is true about Tibia now.

        Forget its window if Tibia has closed, look for a window if none is known,
        and read where its client area is.
        """
        self._game.check_closed()
        self._game.find()
        self._game.current_client()

    def _check_on_delay(self) -> None:
        """Plan the next check for a second from now."""
        self._window.after(ATTACH_POLL_MS, self._check)

    def _check(self) -> None:
        """Look for Tibia again, and tell the app if the state changed."""
        # plan the next check first, so an error in this one cannot stop the checks
        self._check_on_delay()

        previous_state = self.state
        self._look_for_tibia()
        is_changed: bool = self.state != previous_state

        if is_changed:
            self._on_state_changed(self.state)
