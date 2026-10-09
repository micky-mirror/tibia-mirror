"""Colours, fonts and button styles, in a dark and a light theme (Catppuccin Mocha and Latte).

use(name) swaps the module attributes, so read them as `theme.BG` when drawing,
never copy them at import time. The App rebuilds the panel after a switch.
Button styles are in pixels at the current display scaling: call use() after scale.init().
"""

from dataclasses import replace
from typing import TypedDict

from tibia_mirror.ui.base.render import ButtonStyle
from tibia_mirror.ui.base.scale import px


class Palette(TypedDict):
    """A theme's colours ("#rrggbb"), plus how strong its shadows are."""

    BG: str
    MANTLE: str
    CRUST: str
    SURFACE: str
    SURFACE_HI: str
    TEXT: str
    SUBTEXT: str
    OVERLAY: str
    ACCENT: str
    ACCENT_HI: str
    ACCENT_TINT: str
    ON_ACCENT: str
    GREEN: str
    GREEN_HI: str
    RED: str
    RED_HI: str
    YELLOW: str
    GOLD: str
    BLURPLE: str
    KNOB: str
    KNOB_ACTIVE: str
    MIRROR_FRAME: str
    SHADOW: float  # scales every drop shadow


PALETTES: dict[str, Palette] = {
    "dark": {
        "BG": "#1e1e2e",
        "MANTLE": "#181825",  # a step darker than BG: the navigation rail
        "CRUST": "#11111b",  # tooltips
        "SURFACE": "#313244",  # cards, fields
        "SURFACE_HI": "#45475a",  # hover, borders, slider tracks
        "TEXT": "#cdd6f4",
        "SUBTEXT": "#a6adc8",
        "OVERLAY": "#7f849c",  # disabled text
        "ACCENT": "#89b4fa",
        "ACCENT_HI": "#a6c8ff",
        "ACCENT_TINT": "#2f3750",  # ACCENT at 20% over MANTLE: the selected navigation item
        "ON_ACCENT": "#11111b",  # text and knobs on accent-coloured fills
        "GREEN": "#a6e3a1",
        "GREEN_HI": "#bff0bb",
        "RED": "#f38ba8",
        "RED_HI": "#f7a8be",
        "YELLOW": "#f9e2af",  # the unsaved-changes line
        "GOLD": "#f2b84b",  # Tibia Coins in the tip lines; kept apart from YELLOW's warning
        "BLURPLE": "#8c94f7",  # Discord's blurple, lightened to read on BG
        "KNOB": "#cdd6f4",
        "KNOB_ACTIVE": "#ffffff",
        "MIRROR_FRAME": "#a6adc8",
        "SHADOW": 1.0,
    },
    "light": {
        "BG": "#eff1f5",
        "MANTLE": "#e6e9ef",
        "CRUST": "#dce0e8",
        "SURFACE": "#ffffff",
        "SURFACE_HI": "#ccd0da",
        "TEXT": "#4c4f69",
        "SUBTEXT": "#6c6f85",
        "OVERLAY": "#9ca0b0",
        "ACCENT": "#1e66f5",
        "ACCENT_HI": "#4a85f7",
        "ACCENT_TINT": "#becff0",  # ACCENT at 20% over MANTLE
        "ON_ACCENT": "#ffffff",
        "GREEN": "#40a02b",
        "GREEN_HI": "#57b541",
        "RED": "#d20f39",
        "RED_HI": "#e0365a",
        "YELLOW": "#b86e00",  # Latte's yellow is too faint for text on a light background
        "GOLD": "#8f5c00",  # a warm deep gold, dark enough to read on BG and MANTLE
        "BLURPLE": "#4f5bd5",  # Discord's blurple, a touch darker to read on BG
        "KNOB": "#ffffff",
        "KNOB_ACTIVE": "#e6e9ef",
        "MIRROR_FRAME": "#6c6f85",
        "SHADOW": 0.45,  # black shadows read much stronger on a light background
    },
}

# Set by use(); declared here so readers and linters see every name.
BG: str
MANTLE: str
CRUST: str
SURFACE: str
SURFACE_HI: str
TEXT: str
SUBTEXT: str
OVERLAY: str
ACCENT: str
ACCENT_HI: str
ACCENT_TINT: str
ON_ACCENT: str
GREEN: str
GREEN_HI: str
RED: str
RED_HI: str
YELLOW: str
GOLD: str
BLURPLE: str
KNOB: str
KNOB_ACTIVE: str
MIRROR_FRAME: str
SHADOW: float
PRIMARY_BUTTON: ButtonStyle
SECONDARY_BUTTON: ButtonStyle
SAVE_BUTTON: ButtonStyle

# A Tk font as (family, size) or (family, size, style), e.g. ("Segoe UI", 11, "bold").
FontSpec = tuple[str, int] | tuple[str, int, str]

FONT: FontSpec = ("Segoe UI", 10)
FONT_SMALL: FontSpec = ("Segoe UI", 9)
FONT_BOLD: FontSpec = ("Segoe UI Semibold", 10)
FONT_CAPTION: FontSpec = ("Segoe UI Semibold", 9)
FONT_BUTTON: FontSpec = ("Segoe UI", 11, "bold")
FONT_TITLE: FontSpec = ("Segoe UI Semibold", 16)
FONT_ICON: FontSpec = ("Segoe MDL2 Assets", 11)
FONT_ICON_SMALL: FontSpec = ("Segoe MDL2 Assets", 8)
FONT_ICON_LARGE: FontSpec = ("Segoe MDL2 Assets", 16)

# Mirror frame colours sit over the game, so they're the same in both themes.
# "default" is MIRROR_FRAME.
FRAME_COLOR_HEX = {
    "red": "#f38ba8",
    "orange": "#fab387",
    "yellow": "#f9e2af",
    "green": "#a6e3a1",
    "teal": "#94e2d5",
    "blue": "#89b4fa",
    "purple": "#cba6f7",
    "white": "#ffffff",
    "deep_red": "#d20f39",
    "deep_orange": "#fe640b",
    "deep_yellow": "#df8e1d",
    "deep_green": "#40a02b",
    "deep_teal": "#179299",
    "deep_blue": "#1e66f5",
    "deep_purple": "#8839ef",
}


def frame_color(name: str) -> str:
    default: str = globals()["MIRROR_FRAME"]
    return FRAME_COLOR_HEX.get(name, default)


current = ""


def use(name: str) -> None:
    """Switch every colour and button style to the `name` theme ("dark" or "light")."""
    global current
    palette = PALETTES[name]
    secondary = ButtonStyle(
        fill=palette["SURFACE"],
        radius=px(8),
        shadow_alpha=0.45 * palette["SHADOW"],
        shadow_offset=px(2),
        shadow_blur=px(6),
    )
    globals().update(
        palette,
        PRIMARY_BUTTON=ButtonStyle(
            fill=palette["ACCENT"],
            radius=px(10),
            shadow_alpha=0.55 * palette["SHADOW"],
            shadow_offset=px(4),
            shadow_blur=px(10),
        ),
        SECONDARY_BUTTON=secondary,
        SAVE_BUTTON=replace(secondary, fill=palette["GREEN"]),
    )
    current = name


use("dark")
