"""The settings of the app, and the file they are saved in.

SettingsStore holds the settings as they are now. Other classes read them from here,
and change them with update().
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

from tibia_mirror.core import settings


class SettingsStore:
    def __init__(self, file: Path, on_changed: Callable[[], None]) -> None:
        self._file = file
        # Called after every update(). The app uses it to write the file a moment later.
        self._on_changed = on_changed
        # The settings as they are now. If the file is missing or broken, these are the defaults.
        self.current = settings.load(file)

    def update(self, **changes: object) -> None:
        """Change one or more settings, for example update(theme="dark").

        Use the field names of Settings. A wrong name raises TypeError.
        The caller must pass the right type for each value.

        This does not write the file. It tells the app that the settings changed,
        and the app calls save() a short moment later.
        """
        fields: dict[str, Any] = changes
        self.current = replace(self.current, **fields)
        self._on_changed()

    def save(self) -> None:
        """Write the settings to the file. If that fails, this raises OSError."""
        settings.save(self._file, self.current)
