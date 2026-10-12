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
    def __init__(self, file: Path, on_changed: Callable[[AppSettings, AppSettings], None]) -> None:
        self._file = file
        # Called after every change, with the settings before it and after it.
        self._on_changed = on_changed
        # The settings as they are now.
        self.current = self._load()

    def update(self, **new_values: Unpack[AppSettingsUpdate]) -> None:
        """Change one or more settings, for example update(theme="dark")."""
        previous_settings = self.current
        changed_settings = replace(previous_settings, **new_values)

        if changed_settings == previous_settings:
            return

        self.current = changed_settings
        self._on_changed(previous_settings, changed_settings)

    def save(self) -> None:
        """Write the settings to the file. If that fails, this raises OSError."""
        data = self.current.to_json()
        file_content: str = json.dumps(data, indent=2)

        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(file_content, encoding="utf-8")

    def _load(self) -> AppSettings:
        """Read the settings from the file. A missing or broken file gives the defaults."""
        try:
            file_content: str = self._file.read_text(encoding="utf-8")
            data = json.loads(file_content)
        except (OSError, ValueError):
            return AppSettings()
        else:
            return AppSettings.from_json(data)
