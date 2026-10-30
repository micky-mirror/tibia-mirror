"""One profile, as it is saved in its file."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tibia_mirror.core.mirrors.mirror_settings import MirrorSettings

PROFILE_FILE_FORMAT = 2  # the "version" number written into every profile file


@dataclass(frozen=True)
class Profile:
    mirrors: tuple[MirrorSettings, ...] = ()

    @classmethod
    def from_json(cls, data: object) -> Profile:
        """Make the profile from the content of its file.

        If the content is not a good profile, this raises ValueError.
        """
        saved = _SavedProfile(data)

        return cls(mirrors=saved.get_mirrors())

    def to_json(self) -> dict[str, Any]:
        """The profile as it is written to its file."""
        return {
            "version": PROFILE_FILE_FORMAT,
            "mirrors": [mirror.to_json() for mirror in self.mirrors],
        }


class _SavedProfile:
    """A profile file, with one method for each part of the profile."""

    def __init__(self, data: object) -> None:
        # older profile files hold only the list of mirrors
        saved_profile = {"mirrors": data} if isinstance(data, list) else data

        if not isinstance(saved_profile, dict):
            raise ValueError("the profile file is invalid")

        self._data: dict[str, Any] = saved_profile

    def get_mirrors(self) -> tuple[MirrorSettings, ...]:
        """The saved mirrors. If they are missing or wrong, this raises ValueError."""
        value = self._data.get("mirrors")

        if not isinstance(value, list):
            raise ValueError("the profile file is invalid")

        try:
            mirrors = tuple(MirrorSettings.from_json(saved_mirror) for saved_mirror in value)
        except (KeyError, TypeError, AttributeError) as error:
            raise ValueError("the profile file is invalid") from error
        else:
            return mirrors
