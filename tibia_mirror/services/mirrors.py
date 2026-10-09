"""The mirrors on screen: the mirror windows, in the order they were added."""

from __future__ import annotations

from collections.abc import Iterator

from tibia_mirror.ui.overlay.mirror import MirrorWindow


class Mirrors:
    def __init__(self) -> None:
        self._items: list[MirrorWindow] = []

    def __iter__(self) -> Iterator[MirrorWindow]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, mirror: object) -> bool:
        return mirror in self._items

    def append(self, mirror: MirrorWindow) -> None:
        self._items.append(mirror)

    def remove(self, mirror: MirrorWindow) -> None:
        """Take `mirror` out and close its window with a fade."""
        if mirror in self._items:
            self._items.remove(mirror)
        mirror.fade_out_and_destroy()

    def clear(self) -> None:
        """Close every window at once, without the fade."""
        for mirror in self._items:
            mirror.destroy()
        self._items.clear()
