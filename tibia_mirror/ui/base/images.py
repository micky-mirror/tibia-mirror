"""Turning rendered pixel rows into Tk images."""

import tkinter as tk

from tibia_mirror.ui.base.render import (
    Pixels,
    RaisedStyle,
    outlined_pixels,
    raised_pixels,
    rounded_pixels,
)


def _photo(master: tk.Misc, rows: Pixels) -> tk.PhotoImage:
    """A Tk image from pixel rows."""
    img = tk.PhotoImage(master=master, width=len(rows[0]), height=len(rows))
    img.put(" ".join("{" + " ".join(row) + "}" for row in rows))
    return img


def rounded_image(
    master: tk.Misc, *, width: int, height: int, radius: int, colour: str, background: str
) -> tk.PhotoImage:
    """A picture of a box with rounded corners, in `colour`.

    `background` is the colour behind the box: the smooth corners blend into it.
    """
    return _photo(master, rounded_pixels(width, height, radius, colour, background))


def outlined_image(
    master: tk.Misc,
    *,
    width: int,
    height: int,
    radius: int,
    colour: str,
    border: str,
    background: str,
) -> tk.PhotoImage:
    """A picture of a box with rounded corners, in `colour`, with a thin `border`.

    `background` is the colour behind the box: the smooth corners blend into it.
    """
    return _photo(master, outlined_pixels(width, height, radius, colour, border, background))


def raised_image(
    master: tk.Misc,
    *,
    width: int,
    height: int,
    style: RaisedStyle,
    background: str,
    is_pressed: bool = False,
) -> tk.PhotoImage:
    """A picture of a raised box with its soft shadow, sunk while pressed."""
    return _photo(master, raised_pixels(width, height, style, background, is_pressed))
