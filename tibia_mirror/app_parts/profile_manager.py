"""The profiles of the user."""

from pathlib import Path

from tibia_mirror.core.profiles import ProfileStore
from tibia_mirror.settings.app_settings_store import AppSettingsStore


class ProfileManager:
    """Knows which profiles exist and which one is open."""

    def __init__(self, folder: Path, settings: AppSettingsStore) -> None:
        self._folder = folder
        self._settings = settings
        self._store = ProfileStore(folder)
        # the first start has no profile, so an empty "Default" is created
        self._store.ensure_one()
        self._active_name = self._get_start_name()

    @property
    def active_name(self) -> str:
        """The name of the profile that is open."""
        return self._active_name

    def get_names(self) -> list[str]:
        """Read the names of all profiles from the folder, sorted by name."""
        files = self._folder.glob("*.json")
        names = [file.stem for file in files]

        return sorted(names, key=str.casefold)

    def _get_start_name(self) -> str:
        """The profile to open at the start: the one that was open the last time.

        If that profile is gone, it is the first profile of the list.
        """
        names = self.get_names()
        last_name = self._settings.current.last_profile.casefold()

        # Windows file names ignore case, so the names are compared the same way.
        for name in names:
            if name.casefold() == last_name:
                return name

        return names[0]
