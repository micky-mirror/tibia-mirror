"""Small helpers for mirrors: layouts, window sizes, ids, default names and value ranges."""

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from tibia_mirror.config import MIN_OPACITY, ZOOM_RANGE
from tibia_mirror.core.geometry import Rect


def clamp_opacity(value: float) -> float:
    return min(1.0, max(MIN_OPACITY, float(value)))


def clamp_zoom(value: float) -> float:
    lo, hi = ZOOM_RANGE
    return min(hi, max(lo, float(value)))


def next_default_name(existing_names: Iterable[str], stem: str = "Region") -> str:
    """Lowest "<stem> N" not already taken (ignoring case), so defaults stay short and unique."""
    taken = {name.casefold() for name in existing_names}
    number = 1
    while f"{stem} {number}".casefold() in taken:
        number += 1
    return f"{stem} {number}"


def size_key(width: int, height: int) -> str:
    return f"{width}x{height}"


def parse_size_key(key: str) -> tuple[int, int]:
    w, h = (int(side) for side in key.split("x"))
    if w <= 0 or h <= 0:
        # Windows reports a minimized window's client area as 0 x 0; that is no layout.
        raise ValueError(f"not a client size: {key}")
    return w, h


@dataclass(frozen=True)
class Layout:
    region: Rect  # area shown, in client coordinates
    offset: tuple[int, int]  # mirror top-left minus client-area top-left, in screen pixels

    def to_json(self) -> dict[str, Any]:
        region = self.region
        return {"region": [region.x, region.y, region.w, region.h], "offset": list(self.offset)}

    @classmethod
    # Any: parsed JSON, read as if valid; a malformed file raises and the caller reports it.
    def from_json(cls, data: Any) -> "Layout":  # noqa: ANN401
        x, y, w, h = data["region"]
        dx, dy = data.get("offset", (0, 0))
        return cls(Rect(int(x), int(y), int(w), int(h)), (int(dx), int(dy)))


def new_id() -> str:
    return uuid.uuid4().hex
