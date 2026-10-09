"""Pure coordinate math: no Win32 or Tk, so it is unit-testable anywhere."""

from dataclasses import dataclass

# An (x, y) position in pixels.
Point = tuple[int, int]
# A widget's box on screen by its edges, (x0, y0, x1, y1); x1 and y1 exclusive.
Box = tuple[int, int, int, int]


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.right and self.y <= y < self.bottom

    def contains_rect(self, other: "Rect") -> bool:
        return (
            self.x <= other.x
            and other.right <= self.right
            and self.y <= other.y
            and other.bottom <= self.bottom
        )


def rect_from_drag(x0: int, y0: int, x1: int, y1: int) -> Rect:
    """Rect spanned by a drag, whichever direction it went."""
    left, right = sorted((x0, x1))
    top, bottom = sorted((y0, y1))
    return Rect(left, top, right - left, bottom - top)


def panel_geometry(size: tuple[int, int], min_height: int, frame: int, work_area: Rect) -> str:
    """Tk geometry ("WxH+X+Y") centring the panel on the work area, shrunk to fit it."""
    width, wanted_height = size
    height = max(min_height, min(wanted_height, work_area.h - frame))
    x = work_area.x + max(0, (work_area.w - width) // 2)
    y = work_area.y + max(0, (work_area.h - height - frame) // 2)
    return f"{width}x{height}+{x}+{y}"


def fit_panel_size(
    size: tuple[int, int], min_size: tuple[int, int], frame: int, work_area: Rect
) -> tuple[int, int]:
    """A remembered panel size (its inside, without the title bar `frame`), shrunk to fit
    the work area but never below min_size."""
    (width, height), (min_width, min_height) = size, min_size
    return (
        max(min_width, min(width, work_area.w)),
        max(min_height, min(height, work_area.h - frame)),
    )


def nudged_point(pointer: Point, nudge: Point, width: int, height: int) -> Point:
    """The pointer shifted by the arrow keys' nudge, kept on a width x height overlay."""
    (pointer_x, pointer_y), (nudge_x, nudge_y) = pointer, nudge
    x = min(max(pointer_x + nudge_x, 0), width - 1)
    y = min(max(pointer_y + nudge_y, 0), height - 1)
    return x, y


def overlay_to_client(selection: Rect, monitor_origin: Point, client_origin: Point) -> Rect:
    """A selection on the monitor-sized overlay, in the game's client coordinates."""
    monitor_x, monitor_y = monitor_origin
    client_x, client_y = client_origin
    return Rect(
        selection.x + monitor_x - client_x,
        selection.y + monitor_y - client_y,
        selection.w,
        selection.h,
    )


def clamp_rect(rect: Rect, width: int, height: int) -> Rect:
    """`rect` shrunk to fit a width x height area if it must be, then moved inside it."""
    w, h = min(rect.w, width), min(rect.h, height)
    return Rect(min(max(0, rect.x), width - w), min(max(0, rect.y), height - h), w, h)


def resize_around_center(rect: Rect, w: int, h: int, width: int, height: int) -> Rect:
    """A w x h rect with `rect`'s centre, kept inside a width x height area."""
    center_x, center_y = rect.x + rect.w / 2, rect.y + rect.h / 2
    return clamp_rect(Rect(round(center_x - w / 2), round(center_y - h / 2), w, h), width, height)


def clamp_box(x: int, y: int, w: int, h: int, bounds: Rect) -> Point:
    """Top-left of a w x h box at (x, y), moved as little as needed to lie inside `bounds`."""
    return (
        min(max(x, bounds.x), max(bounds.x, bounds.right - w)),
        min(max(y, bounds.y), max(bounds.y, bounds.bottom - h)),
    )


def region_error(
    x: int, y: int, w: int, h: int, width: int, height: int, minimum: int
) -> tuple[str, dict[str, int], str] | None:
    """Why a region doesn't fit the client area, or None.

    Returns (English message with {fields}, their values, the field to fix).
    """
    if not minimum <= w <= width:
        return "Width must be {lo} to {hi} pixels", {"lo": minimum, "hi": width}, "w"
    if not minimum <= h <= height:
        return "Height must be {lo} to {hi} pixels", {"lo": minimum, "hi": height}, "h"
    if not 0 <= x <= width - w:
        return "X must be 0 to {hi} for this width", {"hi": width - w}, "x"
    if not 0 <= y <= height - h:
        return "Y must be 0 to {hi} for this height", {"hi": height - h}, "y"
    return None


def magnifier_source(x: int, y: int, span: int, width: int, height: int) -> Rect:
    """The span x span square to enlarge around (x, y), inside the client area."""
    w, h = min(span, width), min(span, height)
    return Rect(min(max(0, x - span // 2), width - w), min(max(0, y - span // 2), height - h), w, h)


def scaled_size(w: int, h: int, zoom: float) -> tuple[int, int]:
    """Size (w, h) times zoom, at least one pixel each way."""
    return max(1, round(w * zoom)), max(1, round(h * zoom))


def zoom_for_width(width: int, region_width: int, zoom_range: tuple[float, float]) -> float:
    """The zoom that makes a region `region_width` wide show `width` wide, in whole percent."""
    lo, hi = zoom_range
    return min(hi, max(lo, round(width / region_width, 2)))


def scroll_thumb(first: float, last: float, track: int, min_size: int) -> tuple[int, int] | None:
    """(top, height) of a scrollbar thumb for a view of [first, last); None when all fits."""
    visible = last - first
    if visible >= 1:
        return None
    height = min(track, max(min_size, visible * track))
    travel = track - height
    return round(first / (1 - visible) * travel), round(height)


def scroll_fraction(thumb_top: int, thumb_height: int, track: int, visible: float) -> float:
    """The `first` view fraction that puts the thumb's top at `thumb_top`."""
    travel = track - thumb_height
    if travel <= 0:
        return 0.0
    return min(1.0, max(0.0, thumb_top / travel)) * (1 - visible)


def slider_value(x: float, x0: float, x1: float, lo: float, hi: float, step: float) -> float:
    """Value for pointer position x on a slider track spanning x0..x1, snapped to step."""
    fraction = min(1.0, max(0.0, (x - x0) / (x1 - x0)))
    snapped = round((lo + fraction * (hi - lo)) / step) * step
    return round(min(hi, max(lo, snapped)), 4)


def slider_x(value: float, x0: float, x1: float, lo: float, hi: float) -> float:
    """Knob position on a track spanning x0..x1 for `value` (inverse of slider_value)."""
    fraction = min(1.0, max(0.0, (value - lo) / (hi - lo)))
    return x0 + fraction * (x1 - x0)


def place_beside(target: Rect, w: int, h: int, bounds: Rect, gap: int) -> Point:
    """Top-left for a w x h box beside `target`, `gap` away, inside `bounds`.

    Tries right, left, below, then above; if none fits, the right side is clamped.
    """
    candidates = [
        (target.right + gap, target.y),
        (target.x - gap - w, target.y),
        (target.x, target.bottom + gap),
        (target.x, target.y - gap - h),
    ]
    for x, y in candidates:
        if bounds.x <= x and x + w <= bounds.right and bounds.y <= y and y + h <= bounds.bottom:
            return x, y
    x, y = candidates[0]
    return (
        min(max(x, bounds.x), bounds.right - w),
        min(max(y, bounds.y), bounds.bottom - h),
    )
