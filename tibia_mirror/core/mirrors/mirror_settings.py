"""The settings of one mirror."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tibia_mirror.config import DEFAULT_OPACITY, FRAME_COLORS
from tibia_mirror.core.mirrors.mirror_timer import MirrorTimer
from tibia_mirror.core.mirrors.regions import (
    Layout,
    clamp_opacity,
    clamp_zoom,
    new_id,
    parse_size_key,
)


@dataclass(frozen=True)
class MirrorSettings:
    mirror_id: str  # never changes; a paused timer finds its mirror by it
    name: str
    # Which part of the game the mirror shows and where the mirror sits, for each size
    # of the game window. The key is the size as text, for example "1920x1080".
    layouts: dict[str, Layout]
    opacity: float = DEFAULT_OPACITY  # from MIN_OPACITY to 1.0
    zoom: float = 1.0  # 2.0 draws the part of the game two times bigger
    colour: str = FRAME_COLORS[0]  # the name of the frame colour, one of FRAME_COLORS
    is_hidden: bool = False
    is_locked: bool = False  # clicks go through a locked mirror to the game
    timer: MirrorTimer = field(default_factory=MirrorTimer)

    @classmethod
    def from_json(cls, data: object) -> MirrorSettings:
        """Make the settings from one mirror of a profile file.

        A mirror without a name or without a layout raises ValueError.
        """
        saved = _SavedMirror(data)

        return cls(
            mirror_id=saved.get_mirror_id(),
            name=saved.get_name(),
            layouts=saved.get_layouts(),
            opacity=saved.get_opacity(),
            zoom=saved.get_zoom(),
            colour=saved.get_colour(),
            is_hidden=saved.get_bool("hidden"),
            is_locked=saved.get_bool("locked"),
            timer=saved.get_timer(),
        )

    def to_json(self) -> dict[str, Any]:
        """The settings as they are written to a profile file."""
        layouts = {size: self.layouts[size].to_json() for size in sorted(self.layouts)}

        return {
            "id": self.mirror_id,
            "name": self.name,
            "opacity": round(self.opacity, 2),
            "zoom": round(self.zoom, 2),
            "color": self.colour,
            "timer": self.timer.to_json(),
            "hidden": self.is_hidden,
            "locked": self.is_locked,
            "layouts": layouts,
        }


class _SavedMirror:
    """One mirror of a profile file, with one method for each value."""

    def __init__(self, data: object) -> None:
        if not isinstance(data, dict):
            raise ValueError("a mirror must be a JSON object")

        self._data: dict[str, Any] = data

    def get_mirror_id(self) -> str:
        """The saved id. A mirror without one gets a new id."""
        value = self._data.get("id")

        if isinstance(value, str) and value != "":
            return value

        return new_id()

    def get_name(self) -> str:
        value = self._data.get("name")

        if isinstance(value, str) and value != "":
            return value

        raise ValueError("a mirror needs a name")

    def get_layouts(self) -> dict[str, Layout]:
        """The saved layouts. A key that is not a real window size is left out."""
        value = self._data.get("layouts")
        saved_layouts = value if isinstance(value, dict) else {}

        layouts = {
            size: Layout.from_json(layout)
            for size, layout in saved_layouts.items()
            if self._is_window_size(size)
        }

        if not layouts:
            raise ValueError("a mirror needs at least one layout")

        return layouts

    def get_opacity(self) -> float:
        """The saved opacity, moved into the allowed range. If it is not a number, the default."""
        value = self._data.get("opacity")

        if isinstance(value, bool) or not isinstance(value, int | float):
            return MirrorSettings.opacity

        return clamp_opacity(value)

    def get_zoom(self) -> float:
        """The saved zoom, moved into the allowed range. If it is not a number, the default."""
        value = self._data.get("zoom")

        if isinstance(value, bool) or not isinstance(value, int | float):
            return MirrorSettings.zoom

        return clamp_zoom(value)

    def get_colour(self) -> str:
        """The saved colour name if it is one of FRAME_COLORS. If not, the first one."""
        value = self._data.get("color")

        if isinstance(value, str) and value in FRAME_COLORS:
            return value

        return FRAME_COLORS[0]

    def get_bool(self, name: str) -> bool:
        """The saved value if it is true or false. If not, false."""
        value = self._data.get(name)

        if isinstance(value, bool):
            return value

        return False

    def get_timer(self) -> MirrorTimer:
        return MirrorTimer.from_json(self._data.get("timer"))

    def _is_window_size(self, key: str) -> bool:
        """True for a text like "1920x1080" with both numbers above zero."""
        try:
            parse_size_key(key)
        except ValueError:
            return False

        return True
