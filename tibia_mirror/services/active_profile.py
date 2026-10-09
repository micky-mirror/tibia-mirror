"""The active profile.

A profile is a saved set of mirrors. One profile is open at a time: the active profile.
ActiveProfile remembers its name, what was last saved, and if its mirrors are loaded.
"""

from __future__ import annotations

from tibia_mirror.core import regions


class ActiveProfile:
    def __init__(self, name: str) -> None:
        self.name = name
        # The profile as it was last saved or loaded. Used to find unsaved changes.
        self.saved_snapshot = regions.snapshot([])
        # True until the mirrors of this profile are loaded. Loading needs Tibia.
        # If Tibia restarts, the loaded mirrors stay, with their unsaved changes.
        self.needs_load = True
