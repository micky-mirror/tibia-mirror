"""The profiles of the user."""

import json
from collections.abc import Sequence
from pathlib import Path

from tibia_mirror.config import DEFAULT_PROFILE
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.profile import Profile
from tibia_mirror.settings.app_settings_store import AppSettingsStore


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

    def find_name(self, name: str) -> str | None:
        """The profile called `name`, in its own letter case. None if there is none."""
        # Windows file names ignore case, so the names are compared the same way.
        for profile_name in self.get_names():
            if profile_name.casefold() == name.casefold():
                return profile_name

        return None

    def open(self, name: str) -> None:
        """Make the profile `name` the open one, and open it again at the next start."""
        self._active_name = name
        self._settings.update(last_profile=name)

    def rename(self, new_name: str) -> None:
        """Give the open profile a new name.

        If the file cannot be renamed, this raises OSError.
        """
        self._get_file(self._active_name).rename(self._get_file(new_name))
        self.open(new_name)

    def delete(self) -> None:
        """Delete the open profile, then open the first profile left.

        If the file cannot be deleted, this raises OSError.
        """
        self._get_file(self._active_name).unlink(missing_ok=True)
        self.open(self.get_names()[0])

    def read_mirrors(self) -> list[MirrorSettings]:
        """Read the mirrors of the open profile from its file.

        If the file cannot be read, this raises OSError.
        If the file is not a good profile file, this raises ValueError.
        """
        file_content: str = self._get_file(self._active_name).read_text(encoding="utf-8")
        profile = Profile.from_json(json.loads(file_content))

        return list(profile.mirrors)

    def write_mirrors(self, name: str, mirrors: Sequence[MirrorSettings]) -> None:
        """Write the mirrors to the file of the profile `name`.

        If the file cannot be written, this raises OSError.
        """
        profile = Profile(mirrors=tuple(mirrors))
        file_content: str = json.dumps(profile.to_json(), indent=2)

        self._folder.mkdir(parents=True, exist_ok=True)
        self._get_file(name).write_text(file_content, encoding="utf-8")

    def _get_start_name(self) -> str:
        """The profile to open at the start: the one that was open the last time.

        If that profile is gone, it is the first profile of the list.
        """
        last_name = self.find_name(self._settings.current.last_profile)

        if last_name is None:
            return self.get_names()[0]

        return last_name

    def _create_first_profile(self) -> None:
        """Create an empty "Default" profile if there is no profile at all."""
        has_profiles: bool = len(self.get_names()) > 0

        if not has_profiles:
            self.write_mirrors(DEFAULT_PROFILE, [])

    def _get_file(self, name: str) -> Path:
        return self._folder / f"{name}.json"
