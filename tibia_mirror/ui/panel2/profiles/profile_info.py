"""Basic profile data."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileInfo:
    active_name: str
    names: tuple[str, ...]  # sorted by name
