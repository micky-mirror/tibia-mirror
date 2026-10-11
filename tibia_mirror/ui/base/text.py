"""Small helpers for texts: fitting a text into a width, and writing a number as a percent."""

import tkinter.font as tkfont


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
