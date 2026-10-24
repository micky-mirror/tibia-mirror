"""The dark cover where the user drags a box over a part of the game."""

from __future__ import annotations

import tkinter as tk

from tibia_mirror.core.game_window import GameWindow
from tibia_mirror.winapi import win32

COVER_OPACITY = 0.3  # how much the cover darkens the screen under it


class SelectionOverlay(tk.Toplevel):
    """A dark cover over the monitor of the game, for selecting a part of the game."""

    def __init__(self, parent: tk.Misc, game_window: GameWindow) -> None:
        super().__init__(parent)
        self._game_window = game_window
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        self.attributes("-topmost", True)  # above other windows, also above the game
        # window layer setup
        self.attributes("-alpha", COVER_OPACITY)
        self.configure(bg="black", cursor="crosshair")
        # render window over the whole monitor of the game
        self._cover_monitor()
        # take the keys at once, so Escape works without a click first
        self.focus_force()
        self._bind_events()

    def _cover_monitor(self) -> None:
        monitor = win32.monitor_rect(self._game_window.handle)
        self.geometry(f"{monitor.w}x{monitor.h}+{monitor.x}+{monitor.y}")

    def _bind_events(self) -> None:
        self.bind("<Escape>", self._on_escape)
        self.protocol("WM_DELETE_WINDOW", self.destroy)  # Alt+F4

    def _on_escape(self, event: tk.Event[tk.Misc]) -> None:
        self.destroy()
