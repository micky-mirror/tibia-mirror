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
        if not isinstance(data, dict):
            return cls()

        return cls(
            theme=_get_choice(data, "theme", THEMES),
            language=_get_choice(data, "language", LANGUAGES),
            is_panel_on_top=_get_bool(data, "panel_on_top", default=cls.is_panel_on_top),
            is_profile_per_character_on=_get_bool(
                data, "profile_per_character", default=cls.is_profile_per_character_on
            ),
            is_autosave_on=_get_bool(data, "autosave", default=cls.is_autosave_on),
            is_mirror_frame_on=_get_bool(data, "mirror_frame", default=cls.is_mirror_frame_on),
            is_frame_tint_on=_get_bool(data, "frame_tint", default=cls.is_frame_tint_on),
            is_rounded_corners_on=_get_bool(
                data, "rounded_corners", default=cls.is_rounded_corners_on
            ),
            is_fade_on=_get_bool(data, "fades", default=cls.is_fade_on),
        )


def _get_choice(data: dict[str, Any], name: str, choices: Sequence[str]) -> str:
    """The saved text if it is one of the choices. If not, the first choice."""
    value = data.get(name)

    if isinstance(value, str) and value in choices:
        return value

    return choices[0]


def _get_bool(data: dict[str, Any], name: str, *, default: bool) -> bool:
    """The saved value if it is true or false. If not, the default."""
    value = data.get(name)

    if isinstance(value, bool):
        return value

    return default
