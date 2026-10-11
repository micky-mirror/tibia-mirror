"""Turning rendered pixel rows into Tk images."""

import tkinter as tk

from tibia_mirror.ui.base.render import ButtonStyle, Pixels, button_pixels


def photo(master: tk.Misc, rows: Pixels) -> tk.PhotoImage:
    """A PhotoImage from pixel rows as produced by render.button_pixels."""
    img = tk.PhotoImage(master=master, width=len(rows[0]), height=len(rows))
    img.put(" ".join("{" + " ".join(row) + "}" for row in rows))
    return img


def rounded_image(
    master: tk.Misc, *, width: int, height: int, radius: int, colour: str, background: str
) -> tk.PhotoImage:
    """A picture of a box with rounded corners, in `colour`.

    `background` is the colour behind the box: the smooth corners blend into it.
    """
    style = ButtonStyle(fill=colour, radius=radius)
    return photo(master, button_pixels(width, height, style, background))
