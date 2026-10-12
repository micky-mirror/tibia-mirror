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

    @classmethod
    def from_json(cls, data: object) -> AppSettings:
        """Make the settings from the content of settings.json."""
        if not isinstance(data, dict):
            return cls()

        return cls(
            theme=_get_choice(data, "theme", THEMES),
            language=_get_choice(data, "language", LANGUAGES),
            is_panel_on_top=_get_bool(data, "panel_on_top", default=cls.is_panel_on_top),
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
