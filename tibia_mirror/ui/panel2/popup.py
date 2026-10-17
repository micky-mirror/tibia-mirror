"""A small window over the panel that asks for an answer."""

from __future__ import annotations

import tkinter as tk

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.base.scale import px
from tibia_mirror.winapi import dwm, win32

# Sizes at 100% display scaling; px() scales them where they are used.
WIDTH = 340
PAD = 18  # between the sides of the popup and its content
TITLE_GAP = 8  # below the title


class Popup(tk.Toplevel):
    """The base of every dialog of the panel."""

    def __init__(self, window: tk.Misc, title: str) -> None:
        super().__init__(window, bg=theme.BG)
        self.withdraw()  # hidden until it has a size and a place
        self._window = window
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        self.attributes("-topmost", True)  # above the panel and the mirrors, which can be on top
        # rounded corners, a shadow and a thin border, all drawn by Windows
        dwm.round_popup(win32.toplevel_hwnd(self), theme.SURFACE_HI)
        # add popup content
        self._add_title(title)
        self._bind_events()

    def _add_title(self, title: str) -> None:
        label = tk.Label(self, text=title, bg=theme.BG, fg=theme.TEXT, font=theme.FONT_BOLD)
        label.pack(anchor="w", padx=px(PAD), pady=(px(PAD), px(TITLE_GAP)))

    def _open(self) -> None:
        """Show the popup in the middle of the main window, ready for keys."""
        self.update_idletasks()
        width = px(WIDTH)
        height = self.winfo_reqheight()
        position_x = self._window.winfo_rootx() + (self._window.winfo_width() - width) // 2
        position_y = self._window.winfo_rooty() + (self._window.winfo_height() - height) // 2

        self.geometry(f"{width}x{height}+{position_x}+{position_y}")
        self.deiconify()
        self.grab_set()  # the rest of the app takes no clicks or keys until the popup closes
        self.focus_force()

    def _bind_events(self) -> None:
        self.bind("<Escape>", self._on_escape)

    def _on_escape(self, event: tk.Event[tk.Misc]) -> None:
        self.destroy()
