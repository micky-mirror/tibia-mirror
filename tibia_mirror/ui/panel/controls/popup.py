"""A small window over the panel that asks for an answer."""

from __future__ import annotations

import tkinter as tk
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import replace

from tibia_mirror.core.geometry import Point, clamp_box
from tibia_mirror.i18n import tr
from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.render import margins
from tibia_mirror.ui.base.scale import px
from tibia_mirror.ui.panel.controls.widgets import RaisedButton
from tibia_mirror.winapi import dwm, win32

# Sizes at 100% display scaling; px() scales them where they are used.
WIDTH = 396  # the content is as wide as the cards of the Settings page
PAD = 18  # between the sides of the popup and its content
TITLE_GAP = 8  # below the title
BUTTONS_TOP_PAD = 16  # between the content and the buttons
BUTTON_HEIGHT = 34


class Popup(tk.Toplevel, ABC):
    """The base of every dialog of the panel."""

    def __init__(self, window: tk.Misc, title: str) -> None:
        super().__init__(window, bg=theme.BG)
        self.withdraw()  # hidden until it has a size and a place
        self._window = window
        self._content_width = px(WIDTH) - 2 * px(PAD)  # between the two side pads
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        self.attributes("-topmost", True)  # above the panel and the mirrors, which can be on top
        # rounded corners, a shadow and a thin border, all drawn by Windows
        dwm.round_popup(win32.toplevel_hwnd(self), theme.SURFACE_HI)
        # add popup content
        self._add_title(title)
        self._bind_events()

    def _add_title(self, title: str) -> None:
        label = tk.Label(
            self,
            text=title,
            bg=theme.BG,
            fg=theme.TEXT,
            font=theme.FONT_BOLD,
            bd=0,
            padx=0,
            justify="left",
            wraplength=self._content_width,  # a long name goes on to the next line
        )
        label.pack(anchor="w", padx=px(PAD), pady=(px(PAD), px(TITLE_GAP)))

    def _add_buttons(self, ok_text: str, *, is_danger: bool = False) -> None:
        """Cancel and OK, side by side at the bottom.

        The OK button says `ok_text`. A danger one is red, for a step that can't be undone.
        """
        # The button widgets are bigger than the buttons we see: they hold the shadows.
        shadow = margins(theme.SECONDARY_BUTTON)
        row = tk.Frame(self, bg=theme.BG)
        row.pack(
            anchor="w",
            padx=(px(PAD) - shadow.left, 0),
            pady=(px(BUTTONS_TOP_PAD) - shadow.top, px(PAD) - shadow.bottom),
        )

        self._add_button(row, tr("Cancel"), self._cancel, kind="secondary")
        self._add_button(row, ok_text, self._confirm, kind="danger" if is_danger else "primary")

    def _add_button(
        self, row: tk.Frame, text: str, command: Callable[[], None], *, kind: str
    ) -> None:
        """One of two buttons of the same width, with the room for their shadows between them.

        `kind` is "secondary", "primary" or "danger".
        """
        shadow = margins(theme.SECONDARY_BUTTON)
        width = (self._content_width - shadow.left - shadow.right) // 2
        fill, hover_fill, text_colour = {
            "secondary": (theme.SURFACE, theme.SURFACE_HI, theme.TEXT),
            "primary": (theme.ACCENT, theme.ACCENT_HI, theme.ON_ACCENT),
            "danger": (theme.RED, theme.RED_HI, theme.ON_ACCENT),
        }[kind]

        button = RaisedButton(
            row,
            text,
            command,
            width=width,
            height=px(BUTTON_HEIGHT),
            style=replace(theme.SECONDARY_BUTTON, fill=fill),
            hover_fill=hover_fill,
            font=theme.FONT_BOLD,
            fg=text_colour,
            background=theme.BG,
        )
        button.pack(side="left")

    def _open(self) -> None:
        """Show the popup in the middle of the main window, ready for keys."""
        self.update_idletasks()
        width = px(WIDTH)
        height = self.winfo_reqheight()
        position_x, position_y = self._get_position(width, height)

        self.geometry(f"{width}x{height}+{position_x}+{position_y}")
        self.deiconify()
        self.grab_set()  # the rest of the app takes no clicks or keys until the popup closes
        self.focus_force()

    def _get_position(self, width: int, height: int) -> Point:
        """The top-left corner: the middle of the main window, kept on its screen."""
        center_x = self._window.winfo_rootx() + self._window.winfo_width() // 2
        center_y = self._window.winfo_rooty() + self._window.winfo_height() // 2
        work_area = win32.work_area_at((center_x, center_y))

        return clamp_box(center_x - width // 2, center_y - height // 2, width, height, work_area)

    @abstractmethod
    def _confirm(self) -> None:
        """What OK and Enter do. Each dialog keeps its answer and closes itself."""

    def _cancel(self) -> None:
        """What Cancel and Escape do: close the popup without an answer."""
        self.destroy()

    def _bind_events(self) -> None:
        self.bind("<Escape>", self._on_escape)
        self.bind("<Return>", self._on_enter)
        self.bind("<KP_Enter>", self._on_enter)  # the Enter key of the number pad

    def _on_escape(self, event: tk.Event[tk.Misc]) -> None:
        self._cancel()

    def _on_enter(self, event: tk.Event[tk.Misc]) -> None:
        self._confirm()
