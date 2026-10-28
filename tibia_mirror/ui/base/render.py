"""Anti-aliased rounded shapes with soft shadows, rendered pixel by pixel.

Tk's canvas has neither, so images are computed here (pure Python, cached,
unit-tested) and handed to Tk as PhotoImage rows.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from functools import lru_cache

# A colour as (red, green, blue) channels, 0..255; mixing makes them fractional.
Rgb = tuple[float, ...]
# An image as rows of "#rrggbb" strings, top to bottom: what PhotoImage.put takes.
Pixels = tuple[tuple[str, ...], ...]

BLACK: Rgb = (0, 0, 0)


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


@dataclass(frozen=True)
class Box:
    """A box with rounded corners, in pixels from the top left of the picture."""

    left: float
    top: float
    right: float
    bottom: float
    radius: float

    def distance(self, position_x: float, position_y: float) -> float:
        """How far the point is from the edge of the box: below 0 inside it."""
        beyond_x = self._get_beyond_straight_part(position_x, self.left, self.right)
        beyond_y = self._get_beyond_straight_part(position_y, self.top, self.bottom)
        outside = math.hypot(max(beyond_x, 0.0), max(beyond_y, 0.0))
        inside = min(max(beyond_x, beyond_y), 0.0)

        return outside + inside - self.radius

    def is_straight_row(self, position_y: float) -> bool:
        """Whether a pixel row here crosses the box between its rounded corners."""
        return self._get_beyond_straight_part(position_y, self.top, self.bottom) <= -0.5

    def moved_down(self, distance: float) -> Box:
        return replace(self, top=self.top + distance, bottom=self.bottom + distance)

    def _get_beyond_straight_part(self, position: float, start: float, end: float) -> float:
        """How far past the straight part of an edge the position lies, below 0 within it."""
        straight_half = (end - start) / 2 - self.radius
        return abs(position - (start + end) / 2) - straight_half


@dataclass(frozen=True)
class Shadow:
    box: Box
    alpha: float  # how dark the shadow is right under the box, 0..1
    blur: float  # how far it fades out beyond the edge of the box


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
    sink = 1 if pressed else 0
    left, top = margin.left, margin.top + sink
    body = Box(left, top, left + width, top + height, style.radius)

    shadow = None
    if style.shadow_alpha:
        drop = (style.shadow_offset // 2 if pressed else style.shadow_offset) - sink
        alpha = style.shadow_alpha * (0.6 if pressed else 1.0)
        shadow = Shadow(body.moved_down(drop), alpha, style.shadow_blur)

    full_width = margin.left + width + margin.right
    full_height = margin.top + height + margin.bottom
    return _paint(full_width, full_height, background, ((body, style.fill),), shadow)


@lru_cache(maxsize=128)
def outlined_pixels(
    width: int, height: int, radius: int, fill: str, border: str, background: str
) -> Pixels:
    """A rounded box with a 1px `border` over `background`, both edges anti-aliased."""
    outer = Box(0, 0, width, height, radius)
    inner = Box(1, 1, width - 1, height - 1, max(0, radius - 1))

    return _paint(width, height, background, ((outer, border), (inner, fill)))


def _paint(
    width: int,
    height: int,
    background: str,
    layers: tuple[tuple[Box, str], ...],
    shadow: Shadow | None = None,
) -> Pixels:
    """Paint the shadow and then each (box, colour) layer, in order, over `background`."""
    background_rgb = hex_to_rgb(background)
    layers_rgb = [(box, hex_to_rgb(colour)) for box, colour in layers]
    boxes = [box for box, _ in layers] + ([shadow.box] if shadow else [])

    rows: list[tuple[str, ...]] = []
    straight_row: tuple[str, ...] | None = None  # rows between all rounded corners look alike
    for y in range(height):
        center_y = y + 0.5  # measured from the pixel's centre
        is_straight = all(box.is_straight_row(center_y) for box in boxes)
        if is_straight and straight_row is not None:
            rows.append(straight_row)
            continue

        row = tuple(
            rgb_to_hex(_get_colour(x + 0.5, center_y, background_rgb, layers_rgb, shadow))
            for x in range(width)
        )
        rows.append(row)
        if is_straight:
            straight_row = row
    return tuple(rows)


def _get_colour(
    position_x: float,
    position_y: float,
    background: Rgb,
    layers: list[tuple[Box, Rgb]],
    shadow: Shadow | None,
) -> Rgb:
    """The colour of one pixel: the shadow fades out, the edge of a layer covers it partly."""
    colour = background
    if shadow:
        to_shadow = shadow.box.distance(position_x, position_y)
        colour = mix(colour, BLACK, shadow.alpha * shadow_opacity(to_shadow, shadow.blur))

    for box, layer_colour in layers:
        covered = coverage(box.distance(position_x, position_y))
        if covered:
            colour = mix(colour, layer_colour, covered)
    return colour
