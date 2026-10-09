"""The active profile.

A profile is a saved set of mirrors. One profile is open at a time: the active profile.
ActiveProfile remembers its name, what was last saved, and if its mirrors are loaded.
"""

from __future__ import annotations

from collections.abc import Iterable

from tibia_mirror.core import regions
from tibia_mirror.core.profiles import ProfileStore
from tibia_mirror.core.regions import SavedRegion


class ActiveProfile:
    def __init__(self, store: ProfileStore, name: str) -> None:
        self._store = store
        self.name = name
        # The profile as it was last saved or loaded. Used to find unsaved changes.
        self._saved = regions.snapshot([])
        # True until the mirrors of this profile are loaded. Loading needs Tibia.
        # If Tibia restarts, the loaded mirrors stay, with their unsaved changes.
        self.needs_load = True

    def mark_saved(self, mirrors: Iterable[SavedRegion]) -> None:
        """Remember `mirrors` as what is in the profile file now.

        Call it after a save or a load. Pass an empty list if nothing is loaded.
        """
        self._saved = regions.snapshot(mirrors)

    def has_unsaved(self, mirrors: Iterable[SavedRegion]) -> bool:
        """Return True if `mirrors` are different from what was last saved or loaded.

        Pass the mirrors that are on screen now.
        """
        return regions.snapshot(mirrors) != self._saved

    def save(self, mirrors: Iterable[SavedRegion]) -> None:
        """Write `mirrors` to the profile file, and remember them as saved.

        If the file cannot be written, this raises OSError.
        Then nothing is remembered, so the changes stay unsaved.
        """
        mirrors = list(mirrors)
        self._store.save(self.name, mirrors)
        self.mark_saved(mirrors)
