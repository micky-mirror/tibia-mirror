"""Writing the settings to their file."""

import tkinter as tk

from tibia_mirror.config import SETTINGS_SAVE_DELAY_MS
from tibia_mirror.settings.app_settings_store import AppSettingsStore


class SettingsWriter:
    """Writes settings.json."""

    def __init__(self, window: tk.Misc, settings: AppSettingsStore) -> None:
        self._window = window
        self._settings = settings
        self._write_job: str | None = None  # the waiting write, if any

    def write_on_delay(self) -> None:
        """Write settings.json a short moment from now.

        The wait joins many quick changes, like dragging a slider, into one write.
        """
        # throw away the write that is still waiting, if there is one
        if self._write_job is not None:
            self._window.after_cancel(self._write_job)

        # plan a new write for a short moment from now
        self._write_job = self._window.after(SETTINGS_SAVE_DELAY_MS, self._write)

    def _write(self) -> None:
        """Write settings.json now."""
        self._write_job = None
        self._settings.save()
