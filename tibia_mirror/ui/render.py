"""Anti-aliased rounded shapes with soft shadows, rendered pixel by pixel.

Tk's canvas has neither, so images are computed here (pure Python, cached,
unit-tested) and handed to Tk as PhotoImage rows.
"""

import math
from dataclasses import dataclass
from functools import lru_cache

# A colour as (red, green, blue) channels, 0..255; mixing makes them fractional.
Rgb = tuple[float, ...]
# An image as rows of "#rrggbb" strings, top to bottom: what PhotoImage.put takes.
Pixels = tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ButtonStyle:
    fill: str
    radius: int
    shadow_alpha: float = 0.0  # 0 disables the shadow
    shadow_offset: int = 0  # how far the shadow is dropped below the button
    shadow_blur: int = 0  # how far the shadow fades out beyond the button edge


@dataclass(frozen=True)
class Margins:
    """Extra space around the button body that the shadow needs."""

    left: int
    top: int
    right: int
    bottom: int


def margins(style: ButtonStyle) -> Margins:
    blur = style.shadow_blur if style.shadow_alpha else 0
    offset = style.shadow_offset if style.shadow_alpha else 0
    return Margins(blur, max(0, blur - offset), blur, blur + offset)


def hex_to_rgb(color: str) -> Rgb:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Rgb) -> str:
    return "#{:02x}{:02x}{:02x}".format(*(round(channel) for channel in rgb))


def mix(under: Rgb, over: Rgb, alpha: float) -> Rgb:
    """`over` composited onto `under` with the given opacity (0..1)."""
    return tuple(below + (above - below) * alpha for below, above in zip(under, over, strict=True))


def rounded_rect_distance(
    x: float, y: float, x0: float, y0: float, x1: float, y1: float, radius: float
) -> float:
    """Signed distance from (x, y) to a rounded rect: negative inside.

    The standard formula: the distance to the rect shrunk by the radius, minus the radius.
    """
    core_half_w, core_half_h = (x1 - x0) / 2 - radius, (y1 - y0) / 2 - radius
    # How far the point lies beyond the core rect's edges, on each axis (negative: within).
    beyond_x = abs(x - (x0 + x1) / 2) - core_half_w
    beyond_y = abs(y - (y0 + y1) / 2) - core_half_h
    outside = math.hypot(max(beyond_x, 0.0), max(beyond_y, 0.0))
    inside = min(max(beyond_x, beyond_y), 0.0)
    return outside + inside - radius


def coverage(distance: float) -> float:
    """Fraction of a pixel covered by a shape edge at that signed distance."""
    return min(1.0, max(0.0, 0.5 - distance))


def shadow_opacity(distance: float, blur: float) -> float:
    """Gaussian-like falloff from full strength at the edge to ~0 at `blur`."""
    if distance <= 0:
        return 1.0
    if distance >= blur:
        return 0.0
    return math.exp(-3.0 * (distance / blur) ** 2) * (1 - distance / blur)


def in_straight_middle(center_y: float, y0: float, y1: float, radius: float) -> bool:
    """Whether a pixel row lies in the rounded rect's straight middle, clear of its rounded
    top and bottom. The rect covers every row there alike, so one can stand for them all.
    """
    beyond_y = abs(center_y - (y0 + y1) / 2) - ((y1 - y0) / 2 - radius)
    return beyond_y <= -0.5


# Large enough for the opacity slider, whose filled track is rendered once per width.
@lru_cache(maxsize=512)
def button_pixels(
    width: int, height: int, style: ButtonStyle, background: str, pressed: bool = False
) -> Pixels:
    """The button over `background`, with its shadow margins around it.

    Pressed moves the body 1px down and flattens the shadow.
    """
    margin = margins(style)
    background_rgb = hex_to_rgb(background)
    fill_rgb = hex_to_rgb(style.fill)
    black = (0, 0, 0)

    sink = 1 if pressed else 0
    x0, y0 = margin.left, margin.top + sink
    x1, y1 = x0 + width, y0 + height
    shadow_drop = (style.shadow_offset // 2 if pressed else style.shadow_offset) - sink
    shadow_alpha = style.shadow_alpha * (0.6 if pressed else 1.0)

    rows: list[tuple[str, ...]] = []
    middle: tuple[str, ...] | None = None  # a row of the straight middle, once computed
    for y in range(margin.top + height + margin.bottom):
        center_y = y + 0.5  # measured from the pixel's centre
        straight = in_straight_middle(center_y, y0, y1, style.radius) and (
            not shadow_alpha
            or in_straight_middle(center_y, y0 + shadow_drop, y1 + shadow_drop, style.radius)
        )
        if straight and middle is not None:
            rows.append(middle)
            continue
        row: list[str] = []
        for x in range(margin.left + width + margin.right):
            center_x = x + 0.5
            color = background_rgb
            if shadow_alpha:
                to_shadow = rounded_rect_distance(
                    center_x, center_y, x0, y0 + shadow_drop, x1, y1 + shadow_drop, style.radius
                )
                opacity = shadow_alpha * shadow_opacity(to_shadow, style.shadow_blur)
                color = mix(color, black, opacity)
            body = coverage(rounded_rect_distance(center_x, center_y, x0, y0, x1, y1, style.radius))
            if body:
                color = mix(color, fill_rgb, body)
            row.append(rgb_to_hex(color))
        rows.append(tuple(row))
        if straight:
            middle = rows[-1]
    return tuple(rows)


@lru_cache(maxsize=128)
def outlined_pixels(
    width: int, height: int, radius: int, fill: str, border: str, background: str
) -> Pixels:
    """A rounded box with a 1px `border` over `background`, both edges anti-aliased."""
    background_rgb, border_rgb = hex_to_rgb(background), hex_to_rgb(border)
    fill_rgb = hex_to_rgb(fill)
    inner_radius = max(0, radius - 1)
    rows: list[tuple[str, ...]] = []
    middle: tuple[str, ...] | None = None  # a row of the straight middle, once computed
    for y in range(height):
        center_y = y + 0.5  # measured from the pixel's centre
        straight = in_straight_middle(center_y, 0, height, radius) and in_straight_middle(
            center_y, 1, height - 1, inner_radius
        )
        if straight and middle is not None:
            rows.append(middle)
            continue
        row: list[str] = []
        for x in range(width):
            center_x = x + 0.5
            outer = coverage(rounded_rect_distance(center_x, center_y, 0, 0, width, height, radius))
            color = mix(background_rgb, border_rgb, outer)
            inner = coverage(
                rounded_rect_distance(center_x, center_y, 1, 1, width - 1, height - 1, inner_radius)
            )
            row.append(rgb_to_hex(mix(color, fill_rgb, inner)))
        rows.append(tuple(row))
        if straight:
            middle = rows[-1]
    return tuple(rows)
