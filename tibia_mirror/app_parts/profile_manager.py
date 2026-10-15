"""The profiles of the user."""

import json
from collections.abc import Sequence
from pathlib import Path

from tibia_mirror.config import DEFAULT_PROFILE
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.settings.app_settings_store import AppSettingsStore

PROFILE_FILE_FORMAT = 2  # the "version" number written into every profile file


class ProfileManager:
    """Knows which profiles exist and which one is open."""

    def __init__(self, folder: Path, settings: AppSettingsStore) -> None:
        self._folder = folder
        self._settings = settings
        self._create_first_profile()
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

    def read_mirrors(self) -> list[MirrorSettings]:
        """Read the mirrors of the open profile from its file.

        If the file cannot be read, this raises OSError.
        If the file is not a good profile file, this raises ValueError.
        """
        file_content: str = self._get_file(self._active_name).read_text(encoding="utf-8")

        try:
            data = json.loads(file_content)
            saved_mirrors = data if isinstance(data, list) else data["mirrors"]

            return [MirrorSettings.from_json(saved_mirror) for saved_mirror in saved_mirrors]
        except (KeyError, TypeError, AttributeError) as error:
            raise ValueError("the profile file is invalid") from error

    def write_mirrors(self, name: str, mirrors: Sequence[MirrorSettings]) -> None:
        """Write the mirrors to the file of the profile `name`.

        If the file cannot be written, this raises OSError.
        """
        data = {
            "version": PROFILE_FILE_FORMAT,
            "mirrors": [mirror.to_json() for mirror in mirrors],
        }
        file_content: str = json.dumps(data, indent=2)

        self._folder.mkdir(parents=True, exist_ok=True)
        self._get_file(name).write_text(file_content, encoding="utf-8")

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

    def _create_first_profile(self) -> None:
        """Create an empty "Default" profile if there is no profile at all."""
        has_profiles: bool = len(self.get_names()) > 0

        if not has_profiles:
            self.write_mirrors(DEFAULT_PROFILE, [])

    def _get_file(self, name: str) -> Path:
        return self._folder / f"{name}.json"
