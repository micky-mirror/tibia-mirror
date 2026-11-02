"""The dark layer over the main window while a popup is open."""

import tkinter as tk

from tibia_mirror.winapi import dwm, win32

OPACITY = 0.6  # how much the layer darkens the window under it


class Scrim(tk.Toplevel):
    """A dark layer over the whole main window, title bar included."""

    def __init__(self, popup: tk.Misc, window: tk.Misc) -> None:
        super().__init__(popup, bg="black")  # a child of the popup, so it closes with it
        self.withdraw()  # hidden until it has a size and a place
        # basic window configuration
        self.overrideredirect(True)  # no title bar and no borders
        main_window = window.winfo_toplevel()
        self.transient(main_window)  # right above the main window, but not above other apps
        self.attributes("-topmost", main_window.attributes("-topmost"))  # also when it is on top
        # window layer setup
        self.attributes("-alpha", OPACITY)
        dwm.round_like_window(win32.toplevel_hwnd(self))
        # render window over the main window
        self._cover_window(window)

    def _cover_window(self, window: tk.Misc) -> None:
        area = dwm.visible_rect(win32.toplevel_hwnd(window))
        self.geometry(f"{area.w}x{area.h}+{area.x}+{area.y}")
        self.deiconify()
