"""The app's extra top-level windows and close requests.

A close request (Alt+F4 on the active window, or another program asking) makes
Tk destroy the window by default, behind the app's back: a mirror would break, a
dialog would skip its Cancel. So every extra window says what closing it means.
"""

import tkinter as tk


def keep_open(win: tk.Toplevel) -> None:
    """Ignore close requests: only the app removes this window (mirrors, badges, hints)."""
    win.protocol("WM_DELETE_WINDOW", lambda: None)
