"""Watching the clicks and the key presses of the whole computer."""

import time
import tkinter as tk
from collections import deque
from collections.abc import Callable
from functools import partial

from tibia_mirror.config import INPUT_POLL_MS
from tibia_mirror.winapi import win32
from tibia_mirror.winapi.rawinput import RawInputWindow


class InputWatcher:
    """Passes on the left clicks and the key presses of the whole computer."""

    def __init__(
        self,
        window: tk.Misc,
        on_click: Callable[[int, int, float], None],
        on_key: Callable[[int, tuple[str, ...], float], None],
    ) -> None:
        self._window = window
        self._on_click = on_click  # called with the pointer position and the time of the press
        self._on_key = on_key  # called with the key code, the held modifiers and the time
        self._held_keys: set[int] = set()  # the keys that are down now
        self._pending: deque[Callable[[], None]] = deque()  # presses not passed on yet

        # kept, so Windows can call its window procedure for as long as the app runs
        self._raw_input_window = RawInputWindow(self._on_left_down, self._on_key_change)
        self._pass_on_pending()

    def _pass_on_pending(self) -> None:
        # plan the next run first, so an error in a callback cannot stop the runs
        self._window.after(INPUT_POLL_MS, self._pass_on_pending)

        while self._pending:
            pass_on = self._pending.popleft()
            pass_on()

    # Windows calls these two inside Tk's loop, where calling Tk crashes Python: they only note.
    def _on_left_down(self) -> None:
        position_x, position_y = win32.cursor_pos()
        click = partial(self._on_click, position_x, position_y, time.monotonic())
        self._pending.append(click)

    def _on_key_change(self, key_code: int, is_down: bool) -> None:
        if not is_down:
            self._held_keys.discard(key_code)
            return

        # a held key repeats its press, but only the first one counts
        is_repeat = key_code in self._held_keys
        self._held_keys.add(key_code)
        if is_repeat or self._is_modifier(key_code):
            return

        modifiers = self._get_held_modifiers()
        key_press = partial(self._on_key, key_code, modifiers, time.monotonic())
        self._pending.append(key_press)

    def _is_modifier(self, key_code: int) -> bool:
        return any(key_code in codes for codes in win32.MODIFIER_KEYS.values())

    def _get_held_modifiers(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, codes in win32.MODIFIER_KEYS.items()
            if self._held_keys.intersection(codes)
        )
