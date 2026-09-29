"""Display scaling for the app's own pixel sizes.

Fonts are in points, so Tk scales them with Windows' display scaling. Every other
size is written as its value at 100% and goes through px() where it is used, so
boxes grow with the text in them. Game coordinates never go through px().
"""

import math
import tkinter as tk

# Tk's "tk scaling" is pixels per point; at 100% (96 DPI) it is 96 / 72.
_POINTS_AT_100 = 96 / 72

_scale = 1.0


def init(root: tk.Misc) -> None:
    """Read the display scaling Tk uses for fonts. Call once, before building any UI."""
    global _scale
    _scale = float(root.tk.call("tk", "scaling")) / _POINTS_AT_100


def factor() -> float:
    """The display scaling: 1.0 at 100%, 1.25 at 125%, ..."""
    return _scale


def px(size: float) -> int:
    """A size at 100% scaling, in pixels at the current one.

    Halves round away from zero, and a non-zero size never becomes 0.
    """
    if size == 0:
        return 0
    scaled = math.floor(abs(size) * _scale + 0.5)
    return int(math.copysign(max(1, scaled), size))
