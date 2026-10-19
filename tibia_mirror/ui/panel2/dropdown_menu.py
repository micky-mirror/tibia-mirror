"""The menu of a dropdown: a small window with all options, under the box of the dropdown."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Sequence

from tibia_mirror.core.geometry import Box
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.winapi import dwm, win32

# Sizes at 100% display scaling; px() scales them where they are used.
GAP = 4  # between the box of the dropdown and the menu
PAD = 4  # above the first option and below the last one
ROW_HEIGHT = 32  # of one option


class DropdownMenu(tk.Toplevel):
    """The options of a dropdown, in a small window under its box."""

    def __init__(
        self,
        window: tk.Misc,
        options: Sequence[tuple[str, str]],
        selected: str,
        on_pick: Callable[[str], None],
    ) -> None:
        super().__init__(window, bg=theme.SURFACE)
        self.withdraw()  # hidden until it has a size and a place
        self._window = window  # the window under the menu; it gets the focus back
        self._is_window_modal = window.grab_status() is not None  # it gets the grab back too
        # (key, text) of each option, from top to bottom; tkinter itself uses self._options
        self._choices = options
        self._selected = selected  # the key of the chosen option
        self._on_pick = on_pick  # called with the key of the option the user picks
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        self.attributes("-topmost", True)  # above the dialog, which is on top too
        # rounded corners, a shadow and a thin border, all drawn by Windows
        dwm.round_popup(win32.toplevel_hwnd(self), theme.SURFACE_HI)
        self._bind_events()

    def open(self, box: Box, on_close: Callable[[], None]) -> None:
        """Show the menu under `box`, as wide as it. `box` is a place on the screen.

        `on_close` is called when the menu closes.
        """
        self._on_close = on_close
        left, _top, right, bottom = box
        width = right - left
        height = self._get_height()
        position_y = bottom + px(GAP)

        self.geometry(f"{width}x{height}+{left}+{position_y}")
        self.deiconify()
        self.grab_set()  # every click of the app comes to the menu
        self.focus_force()  # the keys come to the menu

    def close(self) -> None:
        """Close the menu, and give the grab and the focus back to the window under it."""
        self.destroy()

        if self._is_window_modal:
            self._window.grab_set()

        self._window.focus_force()
        self._on_close()

    def _get_height(self) -> int:
        """Room for every option, with a pad above and below."""
        return 2 * px(PAD) + len(self._choices) * px(ROW_HEIGHT)

    def _bind_events(self) -> None:
        self.bind("<Escape>", self._on_escape)
        self.protocol("WM_DELETE_WINDOW", self.close)  # Alt+F4

    def _on_escape(self, event: tk.Event[tk.Misc]) -> None:
        self.close()
