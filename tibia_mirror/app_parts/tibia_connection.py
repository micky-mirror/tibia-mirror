"""The connection to Tibia."""

import tkinter as tk
from collections.abc import Callable

from tibia_mirror.app_parts.front_window_tracker import FrontWindowTracker
from tibia_mirror.config import CONNECTION_POLL_MS
from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.core.tibia import characters
from tibia_mirror.core.tibia.connection import CONNECTED, MINIMIZED, WAITING
from tibia_mirror.core.tibia.game_window import GameWindow
from tibia_mirror.winapi import win32
from tibia_mirror.winapi.tibia import find_tibia_window


class Game:
    """The Tibia window.

    Game remembers which window is Tibia and where its client area is.
    The client area is the inside of the window, where the game is drawn.
    It does not include the title bar or the borders.

    Game only reads information about the window. It never changes the window.
    """

    def __init__(self) -> None:
        self.hwnd: Hwnd | None = None  # Tibia's window, None while it is not running
        self.client: Rect | None = None  # its client area on screen, as last seen

    def read_client(self) -> Rect | None:
        """The client area now, or None while it has none (Tibia minimized or gone)."""
        if self.hwnd is None or win32.is_minimized(self.hwnd):
            return None
        client = win32.client_rect(self.hwnd)
        return client if client.w > 0 and client.h > 0 else None

    def current_client(self) -> Rect | None:
        """The client area: read fresh, or as last seen while Tibia is minimized."""
        client = self.read_client()
        if client is not None:
            self.client = client
        return self.client

    def find(self) -> Hwnd | None:
        """Return Tibia's window, or None if Tibia is not running.

        If the window is not known yet, look for it now and remember it.
        """
        if self.hwnd is None:
            self.hwnd = find_tibia_window()
        return self.hwnd

    def check_closed(self) -> bool:
        """Return True one time, when Tibia has just closed, and forget its window.

        There are three cases:
        - Tibia was never found (hwnd is None): return False. Nothing was open, so nothing closed.
        - Tibia is running: return False.
        - Tibia was running and its window is gone: forget the window and return True.

        After True, hwnd is None again. So the next call returns False,
        and find() starts to look for Tibia again.
        """
        if self.hwnd is None or win32.is_window(self.hwnd):
            return False
        self.hwnd = None
        self.client = None
        return True

    @property
    def state(self) -> str:
        """What the panel shows about Tibia: "waiting", "minimized" or "connected".

        - "waiting": Tibia is not found yet.
        - "minimized": Tibia is found, but its client area was never seen,
          because it has been minimized since it was found.
        - "connected": Tibia is found and its client area is known.
        """
        if self.hwnd is None:
            return WAITING
        if self.client is None:
            return MINIMIZED
        return CONNECTED

    def title(self) -> str:
        """Return the title of Tibia's window, or "" if Tibia is not running."""
        return win32.window_title(self.hwnd) if self.hwnd is not None else ""

    def is_minimized(self) -> bool:
        """Return True if Tibia is running and its window is minimized now."""
        return self.hwnd is not None and win32.is_minimized(self.hwnd)


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
