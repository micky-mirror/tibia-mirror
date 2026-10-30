"""The profiles of the user."""

import json
from collections.abc import Callable, Sequence
from dataclasses import fields, replace
from pathlib import Path
from typing import Any

from tibia_mirror.config import DEFAULT_PROFILE
from tibia_mirror.core.keys import KeyCombo
from tibia_mirror.core.mirror_settings import MirrorSettings
from tibia_mirror.core.profile import Profile
from tibia_mirror.core.regions import new_id
from tibia_mirror.settings.app_settings_store import AppSettingsStore


class ProfileManager:
    """Knows which profiles exist, and keeps the open one."""

    def __init__(
        self,
        folder: Path,
        settings: AppSettingsStore,
        on_changed: Callable[[Profile, Profile], None],
    ) -> None:
        self._folder = folder
        self._settings = settings
        self._on_changed = on_changed  # gets the profile before and after each change
        self.current = Profile()  # the open profile, as it is now
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

    def load(self) -> None:
        """Read the open profile from its file into `current`.

        If the file cannot be read, this raises OSError.
        If the file is not a good profile file, this raises ValueError.
        """
        try:
            file_content: str = self._get_file(self._active_name).read_text(encoding="utf-8")
            profile = Profile.from_json(json.loads(file_content))
        except (OSError, ValueError):
            # keep an empty profile, so the last profile is never written into this one
            self.current = Profile()
            raise
        else:
            self.current = profile
            self._clear_hide_all_key_from_mirrors()

    def update_mirror(self, mirror_settings: MirrorSettings) -> None:
        """Give the mirror with the same id these new settings, in the open profile."""
        mirrors = list(self.current.mirrors)

        for index, kept_settings in enumerate(mirrors):
            if kept_settings.mirror_id == mirror_settings.mirror_id:
                mirrors[index] = mirror_settings

        self._set_current(replace(self.current, mirrors=tuple(mirrors)))

    def add_mirror(self, mirror_settings: MirrorSettings) -> None:
        """Add a new mirror to the open profile."""
        mirrors = [*self.current.mirrors, mirror_settings]

        self._set_current(replace(self.current, mirrors=tuple(mirrors)))

    def remove_mirror(self, mirror_id: str) -> None:
        """Take the mirror with this id out of the open profile."""
        mirrors = [
            mirror_settings
            for mirror_settings in self.current.mirrors
            if mirror_settings.mirror_id != mirror_id
        ]

        self._set_current(replace(self.current, mirrors=tuple(mirrors)))

    def clear_hotkey(self, key: KeyCombo) -> None:
        """Set every hotkey that is `key` to None, in the open profile and in the app settings."""
        self._clear_mirror_hotkeys(key)
        self._clear_settings_hotkeys(key)

    def save(self) -> None:
        """Write the open profile to its file. If that fails, this raises OSError."""
        self._write(self._active_name, self.current)

    def write_mirrors(self, name: str, mirrors: Sequence[MirrorSettings]) -> None:
        """Write the mirrors to the file of the profile `name`.

        If the file cannot be written, this raises OSError.
        """
        self._write(name, Profile(mirrors=tuple(mirrors)))

    def duplicate(self, name: str) -> None:
        """Write a copy of the open profile as the profile `name`. Its mirrors get new ids.

        If the file cannot be written, this raises OSError.
        """
        mirrors = [
            replace(mirror_settings, mirror_id=new_id()) for mirror_settings in self.current.mirrors
        ]

        self.write_mirrors(name, mirrors)

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

    def _clear_hide_all_key_from_mirrors(self) -> None:
        """Set every timer hotkey in the open profile that is the hide-all key to None."""
        hide_all_key = self._settings.current.hide_all_key

        if hide_all_key is not None:
            self._clear_mirror_hotkeys(hide_all_key)

    def _clear_mirror_hotkeys(self, key: KeyCombo) -> None:
        """Set every timer hotkey in the open profile that is `key` to None."""
        mirrors = list(self.current.mirrors)

        for index, mirror_settings in enumerate(mirrors):
            if mirror_settings.timer.key == key:
                timer = replace(mirror_settings.timer, key=None)
                mirrors[index] = replace(mirror_settings, timer=timer)

        self._set_current(replace(self.current, mirrors=tuple(mirrors)))

    def _clear_settings_hotkeys(self, key: KeyCombo) -> None:
        """Set every hotkey in the app settings that is `key` to None."""
        app_settings = self._settings.current
        changes: dict[str, Any] = {}

        for setting_field in fields(app_settings):
            if getattr(app_settings, setting_field.name) == key:
                changes[setting_field.name] = None

        self._settings.update(**changes)

    def _set_current(self, profile: Profile) -> None:
        """Keep a changed profile in `current`, and report the change."""
        previous_profile = self.current

        if profile == previous_profile:
            return

        self.current = profile
        self._on_changed(previous_profile, profile)

    def _write(self, name: str, profile: Profile) -> None:
        """Write the profile to the file of the profile `name`. If that fails, OSError."""
        file_content: str = json.dumps(profile.to_json(), indent=2)

        self._folder.mkdir(parents=True, exist_ok=True)
        self._get_file(name).write_text(file_content, encoding="utf-8")

    def _get_file(self, name: str) -> Path:
        return self._folder / f"{name}.json"
