"""The mirrors on the screen."""

import tkinter as tk

from tibia_mirror.settings.app_settings_store import AppSettingsStore
from tibia_mirror.ui.overlay.mirror import MirrorWindow


class MirrorManager:
    """Owns the mirror windows."""

    def __init__(self, window: tk.Misc, settings: AppSettingsStore) -> None:
        self._window = window
        self._settings = settings
        self._mirror_windows: list[MirrorWindow] = []
