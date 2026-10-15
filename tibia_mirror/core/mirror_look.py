"""How every mirror is drawn."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MirrorLook:
    is_frame_on: bool
    is_rounded_on: bool
