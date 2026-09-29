"""Fitting text into a width."""

import tkinter.font as tkfont


def elide(text: str, font: tkfont.Font, max_width: float) -> str:
    """`text` shortened with an ellipsis so it fits in max_width pixels."""
    if font.measure(text) <= max_width:
        return text
    while text and font.measure(text + "…") > max_width:
        text = text[:-1]
    return text + "…"
