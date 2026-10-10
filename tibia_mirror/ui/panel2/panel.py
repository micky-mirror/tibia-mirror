"""The panel: everything inside the main window."""

import tkinter as tk

from tibia_mirror.ui.base import theme
from tibia_mirror.ui.panel2.nav import NavRail


class Panel(tk.Frame):
    """Everything inside the main window."""

    def __init__(self, root: tk.Misc) -> None:
        super().__init__(root, bg=theme.BG)
        NavRail(self).pack(side="left", fill="y")
