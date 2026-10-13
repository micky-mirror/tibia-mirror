"""The settings of one mirror."""

from __future__ import annotations

from dataclasses import dataclass, field

from tibia_mirror.config import DEFAULT_OPACITY, FRAME_COLORS
from tibia_mirror.core.regions import Layout
from tibia_mirror.core.timers import TimerSettings


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
    timer: TimerSettings = field(default_factory=TimerSettings)
