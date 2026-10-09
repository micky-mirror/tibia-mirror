"""The mirrors on screen: the mirror windows, in the order they were added."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Iterator

from tibia_mirror.core.geometry import Rect
from tibia_mirror.core.handles import Hwnd
from tibia_mirror.core.regions import SavedRegion
from tibia_mirror.ui.overlay.mirror import MirrorLook, MirrorWindow


class Mirrors:
    def __init__(
        self,
        root: tk.Misc,
        on_remove: Callable[[MirrorWindow], None],
        on_changed: Callable[[MirrorWindow], None],
    ) -> None:
        self._root = root
        # Handed to every window, which calls them on a right-click remove or after a drag.
        self._on_remove = on_remove
        self._on_changed = on_changed
        self._items: list[MirrorWindow] = []

    def __iter__(self) -> Iterator[MirrorWindow]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, mirror: object) -> bool:
        return mirror in self._items

    def add(
        self, saved: SavedRegion, game: Hwnd, client: Rect, look: MirrorLook
    ) -> MirrorWindow | None:
        """Show a mirror of `saved` on `game`; None if DWM refuses."""
        try:
            mirror = MirrorWindow(
                self._root,
                game,
                saved,
                client,
                look,
                on_remove=self._on_remove,
                on_changed=self._on_changed,
            )
        except OSError:
            return None
        self._items.append(mirror)
        return mirror

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

    def attach(self, game: Hwnd, client: Rect) -> int:
        """Point every mirror at the game's new window; returns how many DWM refused."""
        failed = 0
        for mirror in self._items:
            try:
                mirror.attach(game, client)
            except OSError:
                failed += 1
        return failed

    def detach(self) -> None:
        """The game closed: every mirror lets go of its window."""
        for mirror in self._items:
            mirror.detach()

    def set_client(self, client: Rect) -> None:
        """Move every mirror along with the game's client area."""
        for mirror in self._items:
            mirror.set_client(client)
