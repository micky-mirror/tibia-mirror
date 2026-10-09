"""The settings of the app, and the file they are saved in.

SettingsStore holds the settings as they are now. Other classes read them from here.
"""

from __future__ import annotations

from pathlib import Path

from tibia_mirror.core import settings


class SettingsStore:
    def __init__(self, file: Path) -> None:
        self._file = file
        # The settings as they are now. If the file is missing or broken, these are the defaults.
        self.current = settings.load(file)

    def save(self) -> None:
        """Write the settings to the file. If that fails, this raises OSError."""
        settings.save(self._file, self.current)
