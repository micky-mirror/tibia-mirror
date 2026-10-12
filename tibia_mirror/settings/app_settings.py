"""The settings of the app, as they are saved in settings.json."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from tibia_mirror.config import DEFAULT_OPACITY, DEFAULT_PROFILE, LANGUAGES, THEMES
from tibia_mirror.core import characters
from tibia_mirror.core.characters import Links
from tibia_mirror.core.regions import clamp_opacity
from tibia_mirror.core.timers import (
    KeyCombo,
    Pauses,
    canonical_modifiers,
    parse_key,
    pauses_from_json,
    pauses_to_json,
)

# The place and the size of the panel on the screen: (x, y, width, height).
PanelRect = tuple[int, int, int, int]


@dataclass(frozen=True)
class AppSettings:
    theme: str = THEMES[0]
    language: str = LANGUAGES[0]
    is_panel_on_top: bool = False  # the panel stays above other windows
    # Logging in opens the profile of the character, and creates one the first time.
    is_profile_per_character_on: bool = False
    is_autosave_on: bool = False  # every change to a profile is saved at once
    new_mirror_opacity: float = DEFAULT_OPACITY  # the opacity a new mirror starts with
    is_mirror_frame_on: bool = True  # a grey outline on mirrors without a colour
    is_frame_tint_on: bool = False  # coloured mirrors are also shaded with their colour
    is_rounded_corners_on: bool = False
    is_fade_on: bool = True  # mirrors fade in and out, they do not jump
    last_profile: str = DEFAULT_PROFILE  # the profile that was open, opened again at the start
    # Who logged out last. Their paused timers are shown until somebody logs in.
    last_character: str = ""
    # The key combination that hides every mirror and brings them back. None: no key is set.
    hide_all_key: KeyCombo | None = None
    # Where the panel was when the app closed, to open it there again.
    # None: nothing is saved, and the panel opens in the middle of the screen.
    panel_rect: PanelRect | None = None
    # Which profile each character opens: pairs of (character, profile).
    character_links: Links = ()
    # Where the timers that pause at logout stopped: (character, mirror id, seconds).
    timer_pauses: Pauses = ()

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
            # numbers
            new_mirror_opacity=saved.get_opacity("new_opacity", default=cls.new_mirror_opacity),
            # texts
            last_profile=saved.get_text("profile", default=cls.last_profile),
            last_character=saved.get_text("last_character", default=cls.last_character),
            # keys
            hide_all_key=saved.get_key_combo("hide_all_key", "hide_all_modifiers"),
            # the place of the panel
            panel_rect=saved.get_panel_rect("panel_rect"),
            # lists the app keeps by itself
            character_links=saved.get_character_links("characters"),
            timer_pauses=saved.get_timer_pauses("timer_pauses"),
        )

    def to_json(self) -> dict[str, Any]:
        """The settings as they are written to settings.json."""
        hide_all_key, hide_all_modifiers = self.hide_all_key or (None, ())
        panel_rect = None if self.panel_rect is None else list(self.panel_rect)

        return {
            # choices
            "theme": self.theme,
            "language": self.language,
            # on/off settings
            "panel_on_top": self.is_panel_on_top,
            "profile_per_character": self.is_profile_per_character_on,
            "autosave": self.is_autosave_on,
            "mirror_frame": self.is_mirror_frame_on,
            "frame_tint": self.is_frame_tint_on,
            "rounded_corners": self.is_rounded_corners_on,
            "fades": self.is_fade_on,
            # numbers
            "new_opacity": round(self.new_mirror_opacity, 2),
            # texts
            "profile": self.last_profile,
            "last_character": self.last_character,
            # keys
            "hide_all_key": hide_all_key,
            "hide_all_modifiers": list(hide_all_modifiers),
            # the place of the panel
            "panel_rect": panel_rect,
            # lists the app keeps by itself
            "characters": characters.to_json(self.character_links),
            "timer_pauses": pauses_to_json(self.timer_pauses),
        }


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

    def get_opacity(self, name: str, *, default: float) -> float:
        """The saved number, moved into the allowed range. If it is not a number, the default."""
        value = self._data.get(name)

        if isinstance(value, bool) or not isinstance(value, int | float):
            return default

        return clamp_opacity(value)

    def get_text(self, name: str, *, default: str) -> str:
        """The saved text if it is a text and not empty. If not, the default."""
        value = self._data.get(name)

        if isinstance(value, str) and value != "":
            return value

        return default

    def get_key_combo(self, key_name: str, modifiers_name: str) -> KeyCombo | None:
        """The saved key with the modifiers held with it. None if no key is saved.

        The file keeps the two parts in two places: the code of the key,
        and the list of the modifiers.
        """
        key: int | None = parse_key(self._data.get(key_name))
        modifiers = canonical_modifiers(self._data.get(modifiers_name))

        if key is None:
            return None

        return key, modifiers

    def get_panel_rect(self, name: str) -> PanelRect | None:
        """The saved place and size of the panel. None if they are missing or wrong.

        The file keeps them as a list of four whole numbers: x, y, width, height.
        """
        value = self._data.get(name)

        if not isinstance(value, list) or len(value) != 4:
            return None

        if not all(type(number) is int for number in value):
            return None

        x, y, width, height = value

        if width <= 0 or height <= 0:
            return None

        return x, y, width, height

    def get_character_links(self, name: str) -> Links:
        """The saved links from characters to profiles. Wrong entries are left out."""
        return characters.from_json(self._data.get(name))

    def get_timer_pauses(self, name: str) -> Pauses:
        """The saved moments where the paused timers stopped. Wrong entries are left out."""
        return pauses_from_json(self._data.get(name))
