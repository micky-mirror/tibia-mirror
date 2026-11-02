"""The callback that starts selecting a part of the game for a mirror."""

from typing import Protocol


class SelectAreaCallback(Protocol):
    """Starts selecting the area of a mirror, by drag or by click."""

    def __call__(self, mirror_id: str | None, *, is_by_click: bool) -> None:
        """Start it for the mirror with this id, or for a new mirror when the id is None."""
