"""Small helpers for texts: fitting a text into a width, writing a number as a percent,
and writing out a key combination."""

import tkinter.font as tkfont

from tibia_mirror.core.keys import combo_name
from tibia_mirror.winapi import win32


def elide(text: str, font: tkfont.Font, max_width: float) -> str:
    """`text` shortened with an ellipsis so it fits in max_width pixels."""
    if font.measure(text) <= max_width:
        return text
    while text and font.measure(text + "…") > max_width:
        text = text[:-1]
    return text + "…"


def percent(value: float) -> str:
    """A part of one as a whole percent: 0.5 becomes "50%"."""
    return f"{round(value * 100)}%"


def key_combo_name(value: tuple[int | None, tuple[str, ...]]) -> str:
    """A KeyField value, (virtual-key code or None, modifiers), written out: "Shift+F9"."""
    vk, modifiers = value
    return combo_name(modifiers, "" if vk is None else win32.key_name(vk))
