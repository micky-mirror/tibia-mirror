"""The active profile.

A profile is a saved set of mirrors. One profile is open at a time: the active profile.
ActiveProfile remembers its name, what was last saved, and if its mirrors are loaded.
"""

from __future__ import annotations

from collections.abc import Iterable

from tibia_mirror.core import regions
from tibia_mirror.core.regions import SavedRegion


class ActiveProfile:
    def __init__(self, name: str) -> None:
        self.name = name
        # The profile as it was last saved or loaded. Used to find unsaved changes.
        self._saved = regions.snapshot([])
        # True until the mirrors of this profile are loaded. Loading needs Tibia.
        # If Tibia restarts, the loaded mirrors stay, with their unsaved changes.
        self.needs_load = True

    def mark_saved(self, saved: Iterable[SavedRegion]) -> None:
        """Remember `saved` as what is in the profile file now.

        Call it after a save or a load. Pass an empty list if nothing is loaded.
        """
        self._saved = regions.snapshot(saved)

    def has_unsaved(self, current: Iterable[SavedRegion]) -> bool:
        """Return True if `current` is different from what was last saved or loaded.

        `current` is the mirrors on screen now, in their saved form.
        """
        return regions.snapshot(current) != self._saved
