"""Saved mirrors and their JSON profile format (SavedRegion.to_json shows every field).

Older files, from before layouts or mirror ids, still load.
"""

import json
import math
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from tibia_mirror.config import (
    DEFAULT_MIRROR_POS,
    DEFAULT_OPACITY,
    FRAME_COLORS,
    MIN_OPACITY,
    ZOOM_RANGE,
)
from tibia_mirror.core.geometry import Rect, clamp_rect
from tibia_mirror.core.timers import TimerSettings

FORMAT_VERSION = 2


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


def _valid_key(key: object) -> bool:
    """Whether a layout key names a real client size; others are skipped on load."""
    try:
        parse_size_key(str(key))
    except ValueError:
        return False
    return True


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


def guess_layout(layouts: dict[str, Layout], width: int, height: int) -> Layout:
    """A first layout for a new client size, from the closest known one.

    The region keeps its size (Tibia's panels don't scale) while its position and
    the mirror's offset move proportionally.
    """

    def distance(key: str) -> float:
        known_w, known_h = parse_size_key(key)
        return abs(math.log(width / known_w)) + abs(math.log(height / known_h))

    closest = min(layouts, key=distance)
    closest_w, closest_h = parse_size_key(closest)
    scale_x, scale_y = width / closest_w, height / closest_h
    source = layouts[closest]
    known = source.region
    center_x = (known.x + known.w / 2) * scale_x
    center_y = (known.y + known.h / 2) * scale_y
    moved = Rect(round(center_x - known.w / 2), round(center_y - known.h / 2), known.w, known.h)
    offset = (round(source.offset[0] * scale_x), round(source.offset[1] * scale_y))
    return Layout(clamp_rect(moved, width, height), offset)


@dataclass(frozen=True)
class SavedRegion:
    name: str
    layouts: dict[str, Layout] = field(default_factory=dict)  # size_key -> Layout
    opacity: float = DEFAULT_OPACITY
    hidden: bool = False
    locked: bool = False
    zoom: float = 1.0
    color: str = FRAME_COLORS[0]  # frame colour name
    timer: TimerSettings = field(default_factory=TimerSettings)
    # Permanent and hidden: settings.json keys timers' paused progress by it.
    # "" until assign_ids gives it one.
    id: str = ""

    def to_json(self) -> dict[str, Any]:
        data = {} if not self.id else {"id": self.id}
        return data | {
            "name": self.name,
            "opacity": round(self.opacity, 2),
            "zoom": round(self.zoom, 2),
            "color": self.color,
            "timer": self.timer.to_json(),
            "hidden": self.hidden,
            "locked": self.locked,
            "layouts": {size: self.layouts[size].to_json() for size in sorted(self.layouts)},
        }

    @classmethod
    def from_json(
        cls,
        data: Any,  # noqa: ANN401 - parsed JSON, as in Layout.from_json
        default_name: str,
        client: Rect | None = None,
    ) -> "SavedRegion":
        """`client` (the client area as a screen Rect) is needed only for pre-layout entries."""
        if "layouts" in data:
            layouts = {
                str(size): Layout.from_json(layout)
                for size, layout in data["layouts"].items()
                if _valid_key(size)
            }
        else:
            if client is None or client.w <= 0 or client.h <= 0:
                raise ValueError("an entry without layouts needs the client area's size")
            x, y, w, h = data["region"]
            pos_x, pos_y = data.get("pos", DEFAULT_MIRROR_POS)
            layouts = {
                size_key(client.w, client.h): Layout(
                    Rect(int(x), int(y), int(w), int(h)),
                    (int(pos_x) - client.x, int(pos_y) - client.y),
                )
            }
        if not layouts:
            raise ValueError("a mirror needs at least one layout")
        return cls(
            name=data.get("name", default_name),
            layouts=layouts,
            opacity=clamp_opacity(data.get("opacity", DEFAULT_OPACITY)),
            hidden=bool(data.get("hidden", False)),
            locked=bool(data.get("locked", False)),
            zoom=clamp_zoom(data.get("zoom", 1.0)),
            color=data["color"] if data.get("color") in FRAME_COLORS else FRAME_COLORS[0],
            timer=TimerSettings.from_json(data.get("timer")),
            id=data["id"] if isinstance(data.get("id"), str) else "",
        )


def new_id() -> str:
    return uuid.uuid4().hex


def assign_ids(regions: Iterable[SavedRegion]) -> tuple[list[SavedRegion], bool]:
    """The regions, each with an id; and whether any lacked one (from before ids)."""
    regions = list(regions)
    missing = any(not region.id for region in regions)
    with_ids = [region if region.id else replace(region, id=new_id()) for region in regions]
    return with_ids, missing


def snapshot(regions: Iterable[SavedRegion]) -> dict[str, Any]:
    """Exactly what save() writes, so comparing snapshots ignores float noise
    below the stored precision (a slider dragged back reads as unchanged)."""
    return {"version": FORMAT_VERSION, "mirrors": [region.to_json() for region in regions]}


def save(path: Path, regions: Iterable[SavedRegion]) -> None:
    path.write_text(json.dumps(snapshot(regions), indent=2), encoding="utf-8")


def load(path: Path, client: Rect | None = None) -> list[SavedRegion]:
    """The regions in a profile file; see from_json for `client`."""
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data if isinstance(data, list) else data["mirrors"]
    return [
        SavedRegion.from_json(entry, default_name=f"Region {number}", client=client)
        for number, entry in enumerate(entries, start=1)
    ]
