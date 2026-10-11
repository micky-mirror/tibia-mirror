"""What the Mirrors page knows about one mirror."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MirrorInfo:
    """What the Mirrors page shows about one mirror."""

    name: str
    area_width: int  # of the mirrored part of the game, in pixels
    area_height: int
    opacity: float  # from 0.0 to 1.0
    colour: str  # the name of the frame colour, one of config.FRAME_COLORS
    is_hidden: bool
    is_locked: bool
    is_timer_on: bool
