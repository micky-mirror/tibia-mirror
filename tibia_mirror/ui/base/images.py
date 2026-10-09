"""Turning rendered pixel rows into Tk images."""

import tkinter as tk

from tibia_mirror.ui.base.render import Pixels


def photo(master: tk.Misc, rows: Pixels) -> tk.PhotoImage:
    """A PhotoImage from pixel rows as produced by render.button_pixels."""
    img = tk.PhotoImage(master=master, width=len(rows[0]), height=len(rows))
    img.put(" ".join("{" + " ".join(row) + "}" for row in rows))
    return img
