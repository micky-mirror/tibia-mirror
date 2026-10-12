"""The settings of the app, as they are saved in settings.json."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from tibia_mirror.config import LANGUAGES, THEMES


@dataclass(frozen=True)
class AppSettings:
    theme: str = THEMES[0]
    language: str = LANGUAGES[0]
    is_panel_on_top: bool = False  # the panel stays above other windows
    # Logging in opens the profile of the character, and creates one the first time.
    is_profile_per_character_on: bool = False
    is_autosave_on: bool = False  # every change to a profile is saved at once
    is_mirror_frame_on: bool = True  # a grey outline on mirrors without a colour
    is_frame_tint_on: bool = False  # coloured mirrors are also shaded with their colour
    is_rounded_corners_on: bool = False
    is_fade_on: bool = True  # mirrors fade in and out, they do not jump

    @classmethod
    def from_json(cls, data: object) -> AppSettings:
        """Make the settings from the content of settings.json."""
        saved = _SavedData(data)

        return cls(
            # choices
            theme=saved.get_choice("theme", THEMES),
            language=saved.get_choice("language", LANGUAGES),
            # on/off settings
            is_panel_on_top=saved.get_bool("panel_on_top", default=cls.is_panel_on_top),
            is_profile_per_character_on=saved.get_bool(
                "profile_per_character", default=cls.is_profile_per_character_on
            ),
            is_autosave_on=saved.get_bool("autosave", default=cls.is_autosave_on),
            is_mirror_frame_on=saved.get_bool("mirror_frame", default=cls.is_mirror_frame_on),
            is_frame_tint_on=saved.get_bool("frame_tint", default=cls.is_frame_tint_on),
            is_rounded_corners_on=saved.get_bool(
                "rounded_corners", default=cls.is_rounded_corners_on
            ),
            is_fade_on=saved.get_bool("fades", default=cls.is_fade_on),
        )


class _SavedData:
    """The content of settings.json, with one method for each kind of value.

    A value that is missing or wrong in the file is replaced by its default.
    """

    def __init__(self, data: object) -> None:
        # Content that is not a JSON object is read as an empty one.
        self._data: dict[str, Any] = data if isinstance(data, dict) else {}

    def get_choice(self, name: str, choices: Sequence[str]) -> str:
        """The saved text if it is one of the choices. If not, the first choice."""
        value = self._data.get(name)

        if isinstance(value, str) and value in choices:
            return value

        return choices[0]

    def get_bool(self, name: str, *, default: bool) -> bool:
        """The saved value if it is true or false. If not, the default."""
        value = self._data.get(name)

        if isinstance(value, bool):
            return value

        return default
