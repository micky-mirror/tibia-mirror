"""The menu of a dropdown: a small window with all options, under the box of the dropdown."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from tibia_mirror.core.geometry import Box
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.images import rounded_image
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
HIGHLIGHT_RADIUS = 6  # of the rounded corners of the highlight behind a hovered option
HIGHLIGHT_GAP = 1  # above and below the highlight, so two rows never touch


@dataclass(frozen=True)
class MenuOption:
    """One option of a dropdown menu."""

    key: str  # what the menu hands over when the option is picked
    text: str
    text_colour: str | None = None  # a theme colour; None draws the text in theme.TEXT


def get_menu_width(options: Sequence[MenuOption]) -> int:
    """The width the menu needs for its longest option."""
    font = tkfont.Font(font=theme.FONT)
    longest = max(font.measure(option.text) for option in options)

    return px(PAD + TEXT_X) + longest + px(TEXT_ROOM + PAD)


class DropdownMenu(tk.Toplevel):
    """The options of a dropdown, in a small window under its box."""

    def __init__(
        self,
        window: tk.Misc,
        options: Sequence[MenuOption],
        selected: str,
        on_pick: Callable[[str], None],
    ) -> None:
        super().__init__(window, bg=theme.SURFACE)
        self.withdraw()  # hidden until it has a size and a place
        self._window = window  # the window under the menu; it gets the focus back
        self._is_window_modal = window.grab_status() is not None  # it gets the grab back too
        # the options, from top to bottom; tkinter itself uses self._options
        self._choices = options
        self._selected = selected  # the key of the chosen option
        self._on_pick = on_pick  # called with the key of the option the user picks
        self._hovered_index: int | None = None  # the option under the pointer
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

        self._draw_highlight(width)
        self.geometry(f"{width}x{height}+{left}+{position_y}")
        self.deiconify()
        self.grab_set()  # every click of the app comes to the menu
        self.focus_force()  # the keys come to the menu

    def close(self) -> None:
        """Close the menu, and give the grab and the focus back to the window under it."""
        self._close_window()
        self._window.focus_force()

    def _close_window(self) -> None:
        """Close the menu, and give the grab back to the window under it."""
        self.destroy()

        if self._is_window_modal:
            self._window.grab_set()

        self._on_close()

    def _add_canvas(self) -> None:
        """The surface the options are drawn on. It fills the whole menu."""
        self._canvas = tk.Canvas(self, bg=theme.SURFACE, highlightthickness=0, bd=0)
        self._canvas.pack(fill="both", expand=True)

    def _draw_options(self) -> None:
        """Each option in its own row, with a check mark at the chosen one."""
        for index, option in enumerate(self._choices):
            middle_y = self._get_row_middle_y(index)
            self._draw_text(option, middle_y)

            if option.key == self._selected:
                self._draw_check(middle_y)

    def _draw_text(self, option: MenuOption, middle_y: int) -> None:
        self._canvas.create_text(
            px(PAD + TEXT_X),
            middle_y,
            text=option.text,
            anchor="w",
            font=theme.FONT,
            fill=option.text_colour or theme.TEXT,
        )

    def _draw_check(self, middle_y: int) -> None:
        self._canvas.create_text(
            px(PAD + CHECK_X),
            middle_y,
            text=CHECK,
            font=theme.FONT_ICON,
            fill=theme.ACCENT,
        )

    def _draw_highlight(self, width: int) -> None:
        """The lighter shape behind the hovered option, hidden until an option is hovered."""
        self._highlight_image = rounded_image(
            self._canvas,
            width=width - 2 * px(PAD),
            height=px(ROW_HEIGHT) - 2 * px(HIGHLIGHT_GAP),
            radius=px(HIGHLIGHT_RADIUS),
            colour=theme.SURFACE_HI,
            background=theme.SURFACE,
        )
        self._highlight = self._canvas.create_image(
            px(PAD), 0, anchor="nw", image=self._highlight_image, state="hidden"
        )
        # the options are drawn first, so the highlight must go under them
        self._canvas.tag_lower(self._highlight)

    def _get_row_top_y(self, index: int) -> int:
        """The top of the row of the option at `index`, from the top of the menu."""
        return px(PAD) + index * px(ROW_HEIGHT)

    def _get_row_middle_y(self, index: int) -> int:
        """The middle of the row of the option at `index`, from the top of the menu."""
        return self._get_row_top_y(index) + px(ROW_HEIGHT) // 2

    def _get_index_at(self, position_y: int) -> int | None:
        """The index of the option at this height. None between the options and the edges."""
        if position_y < px(PAD):
            return None

        index = (position_y - px(PAD)) // px(ROW_HEIGHT)

        if index >= len(self._choices):
            return None

        return index

    def _get_next_index(self, step: int) -> int:
        """The option `step` rows away from the hovered one, going round at the ends."""
        if self._hovered_index is None:
            return 0 if step > 0 else len(self._choices) - 1

        return (self._hovered_index + step) % len(self._choices)

    def _is_inside(self, position_x: int, position_y: int) -> bool:
        """Whether this place on the screen is on the menu."""
        left = self.winfo_rootx()
        top = self.winfo_rooty()
        is_inside_x: bool = left <= position_x < left + self.winfo_width()
        is_inside_y: bool = top <= position_y < top + self.winfo_height()

        return is_inside_x and is_inside_y

    def _get_height(self) -> int:
        """Room for every option, with a pad above and below."""
        return 2 * px(PAD) + len(self._choices) * px(ROW_HEIGHT)

    def _bind_events(self) -> None:
        self.bind("<Escape>", self._on_escape)
        self.bind("<Up>", self._on_up)
        self.bind("<Down>", self._on_down)
        self.bind("<Return>", self._on_enter)
        self.bind("<KP_Enter>", self._on_enter)  # the Enter key of the number pad
        self.bind("<ButtonRelease>", self._on_mouse_up)
        self.bind("<FocusOut>", self._on_focus_out)
        self.protocol("WM_DELETE_WINDOW", self.close)  # Alt+F4
        # <Enter> too: the pointer can come in and stop, with no <Motion> after it.
        self._canvas.bind("<Enter>", self._on_mouse_move)
        self._canvas.bind("<Motion>", self._on_mouse_move)
        self._canvas.bind("<Leave>", self._on_mouse_leave)

    def _on_escape(self, event: tk.Event[tk.Misc]) -> None:
        self.close()

    def _on_up(self, event: tk.Event[tk.Misc]) -> None:
        self._set_hovered(self._get_next_index(-1))

    def _on_down(self, event: tk.Event[tk.Misc]) -> None:
        self._set_hovered(self._get_next_index(1))

    def _on_enter(self, event: tk.Event[tk.Misc]) -> None:
        if self._hovered_index is not None:
            self._pick(self._hovered_index)

    def _on_mouse_up(self, event: tk.Event[tk.Misc]) -> None:
        # the menu holds the grab, so every click of the app ends here
        position_y = event.y_root - self.winfo_rooty()
        index = self._get_index_at(position_y)

        if not self._is_inside(event.x_root, event.y_root):
            self.close()
        elif index is not None:
            self._pick(index)

    def _on_focus_out(self, event: tk.Event[tk.Misc]) -> None:
        # another app has the focus now, so the menu closes and leaves the focus there
        if event.widget is self:
            self._close_window()

    def _on_mouse_move(self, event: tk.Event[tk.Canvas]) -> None:
        self._set_hovered(self._get_index_at(event.y))

    def _on_mouse_leave(self, event: tk.Event[tk.Canvas]) -> None:
        self._set_hovered(None)

    def _pick(self, index: int) -> None:
        """Close the menu, then hand over the key of the option at `index`."""
        key = self._choices[index].key

        self.close()
        self._on_pick(key)

    def _set_hovered(self, index: int | None) -> None:
        self._hovered_index = index
        self._update_highlight()
        self._update_cursor()

    def _update_highlight(self) -> None:
        """Show the highlight behind the hovered option, or hide it when none is hovered."""
        if self._hovered_index is None:
            self._canvas.itemconfigure(self._highlight, state="hidden")
            return

        top_y = self._get_row_top_y(self._hovered_index) + px(HIGHLIGHT_GAP)

        self._canvas.coords(self._highlight, px(PAD), top_y)
        self._canvas.itemconfigure(self._highlight, state="normal")

    def _update_cursor(self) -> None:
        """Show a hand over an option."""
        cursor = "" if self._hovered_index is None else "hand2"

        self._canvas.configure(cursor=cursor)
