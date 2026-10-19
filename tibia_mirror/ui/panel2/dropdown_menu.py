"""The menu of a dropdown: a small window with all options, under the box of the dropdown."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Sequence

from tibia_mirror.core.geometry import Box
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.winapi import dwm, win32

CHECK = "\ue73e"  # a check mark, from the Segoe MDL2 Assets icon font

# Sizes at 100% display scaling; px() scales them where they are used.
GAP = 4  # between the box of the dropdown and the menu
PAD = 4  # around the options, inside the menu
ROW_HEIGHT = 32  # of one option
CHECK_X = 16  # from PAD to the middle of the check mark
TEXT_X = 32  # from PAD to the start of the text
TEXT_ROOM = 8  # kept free after the longest text, before PAD


def get_menu_width(options: Sequence[tuple[str, str]]) -> int:
    """The width the menu needs for its longest option."""
    font = tkfont.Font(font=theme.FONT)
    longest = max(font.measure(text) for _key, text in options)

    return px(PAD + TEXT_X) + longest + px(TEXT_ROOM + PAD)


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
        # add menu content
        self._add_canvas()
        self._draw_options()
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

    def _add_canvas(self) -> None:
        """The surface the options are drawn on. It fills the whole menu."""
        self._canvas = tk.Canvas(self, bg=theme.SURFACE, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True)

    def _draw_options(self) -> None:
        """Each option in its own row, with a check mark at the chosen one."""
        for index, (key, text) in enumerate(self._choices):
            middle_y = self._get_row_middle_y(index)
            self._draw_text(text, middle_y)

            if key == self._selected:
                self._draw_check(middle_y)

    def _draw_text(self, text: str, middle_y: int) -> None:
        self._canvas.create_text(
            px(PAD + TEXT_X),
            middle_y,
            text=text,
            anchor="w",
            font=theme.FONT,
            fill=theme.TEXT,
        )

    def _draw_check(self, middle_y: int) -> None:
        self._canvas.create_text(
            px(PAD + CHECK_X),
            middle_y,
            text=CHECK,
            font=theme.FONT_ICON,
            fill=theme.ACCENT,
        )

    def _get_row_middle_y(self, index: int) -> int:
        """The middle of the row of the option at `index`, from the top of the menu."""
        return px(PAD) + index * px(ROW_HEIGHT) + px(ROW_HEIGHT) // 2

    def _get_height(self) -> int:
        """Room for every option, with a pad above and below."""
        return 2 * px(PAD) + len(self._choices) * px(ROW_HEIGHT)

    def _bind_events(self) -> None:
        self.bind("<Escape>", self._on_escape)
        self.protocol("WM_DELETE_WINDOW", self.close)  # Alt+F4

    def _on_escape(self, event: tk.Event[tk.Misc]) -> None:
        self.close()
