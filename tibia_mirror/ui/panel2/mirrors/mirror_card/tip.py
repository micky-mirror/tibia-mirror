"""The texts of a hint: the small window that opens under a thing the pointer rests on."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tip:
    """The texts of one hint."""

    title: str  # what a click does, such as "Lock mirror"
    detail: str = ""  # one more line that explains it; "" for none
