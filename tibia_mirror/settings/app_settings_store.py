"""The settings of the app while it runs, and the file they are saved in.

AppSettingsStore holds the settings as they are now. Other classes read them from here,
and change them with update().
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from tibia_mirror.settings.app_settings import AppSettings, AppSettingsUpdate

if TYPE_CHECKING:
    # Only the type checker reads this line. The running app does not need the package.
    from typing_extensions import Unpack


class AppSettingsStore:
    def __init__(self, file: Path, on_changed: Callable[[], None]) -> None:
        self._file = file
        # Called after every change. The app uses it to write the file a moment later.
        self._on_changed = on_changed
        # The settings as they are now.
        self.current = self._load()

    def update(self, **new_values: Unpack[AppSettingsUpdate]) -> None:
        """Change one or more settings, for example update(theme="dark")."""
        changed_settings = replace(self.current, **new_values)

        if changed_settings == self.current:
            return

        self.current = changed_settings
        self._on_changed()

    def _load(self) -> AppSettings:
        """Read the settings from the file. A missing or broken file gives the defaults."""
        try:
            file_content: str = self._file.read_text(encoding="utf-8")
            data = json.loads(file_content)
        except (OSError, ValueError):
            return AppSettings()
        else:
            return AppSettings.from_json(data)
