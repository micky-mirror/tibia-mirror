"""What the Mirrors page knows about one mirror."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MirrorInfo:
    """What the Mirrors page shows about one mirror."""

    name: str
    width: int  # of the mirrored area, in pixels
    height: int  # of the mirrored area, in pixels
    opacity: float  # from 0.0 to 1.0
    colour: str  # the colour of the frame, "" for none
    is_hidden: bool
    is_locked: bool
