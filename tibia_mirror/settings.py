"""App-wide preferences, saved to settings.json as soon as they change.

Unknown keys are ignored and bad values fall back to defaults, so a hand-edited
file never stops the app from starting.
"""

import json
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path
from typing import Any

from tibia_mirror import characters
from tibia_mirror.characters import Links
from tibia_mirror.config import DEFAULT_OPACITY, DEFAULT_PROFILE, LANGUAGES, THEMES
from tibia_mirror.regions import clamp_opacity
from tibia_mirror.timers import (
    KeyCombo,
    Pauses,
    canonical_modifiers,
    parse_key,
    pauses_from_json,
    pauses_to_json,
)

# Fields with their own JSON format, which the generic checks in from_json skip.
_OWN_FORMAT_FIELDS = (
    "hide_all_key",
    "hide_all_modifiers",
    "characters",
    "timer_pauses",
    "panel_rect",
)

# The panel's place and size, as Tk's geometry has them: (x, y, width, height).
PanelRect = tuple[int, int, int, int]


@dataclass(frozen=True)
class Settings:
    autosave: bool = False
    new_opacity: float = DEFAULT_OPACITY  # starting opacity of newly added mirrors
    mirror_frame: bool = True
    fades: bool = True
    panel_on_top: bool = False
    rounded_corners: bool = False
    frame_tint: bool = False  # coloured mirrors are also shaded with their colour
    theme: str = THEMES[0]
    language: str = LANGUAGES[0]
    profile: str = DEFAULT_PROFILE  # the active profile, restored on the next start
    # Logging in opens the character's linked profile, creating one the first time.
    profile_per_character: bool = False
    characters: Links = ()  # (character, profile) pairs, see characters.py
    # Where the timers that pause while logged out stopped, per character (see timers.py).
    timer_pauses: Pauses = ()
    last_character: str = ""  # who logged out last: their paused timers show until a login
    # The key combination that hides every mirror and brings them back (None: not set).
    hide_all_key: int | None = None  # Windows virtual-key code
    hide_all_modifiers: tuple[str, ...] = ()  # held with it, from timers.MODIFIERS
    # Where the panel was last, to open there again (None: centred on the screen).
    panel_rect: PanelRect | None = None

    @property
    def hide_all_combo(self) -> KeyCombo | None:
        """The hide-all key as a (virtual-key code, modifiers) pair, or None."""
        if self.hide_all_key is None:
            return None
        return (self.hide_all_key, self.hide_all_modifiers)

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["new_opacity"] = round(self.new_opacity, 2)
        data["hide_all_modifiers"] = list(self.hide_all_modifiers)
        data["characters"] = characters.to_json(self.characters)
        data["timer_pauses"] = pauses_to_json(self.timer_pauses)
        data["panel_rect"] = None if self.panel_rect is None else list(self.panel_rect)
        return data

    @classmethod
    def from_json(cls, data: object) -> "Settings":
        if not isinstance(data, dict):
            return cls()
        values: dict[str, Any] = {}
        for field in fields(cls):
            if field.name in _OWN_FORMAT_FIELDS:
                continue
            value = data.get(field.name)
            # bool is an int subclass, so check it first and keep numbers numeric.
            if isinstance(field.default, bool):
                ok = isinstance(value, bool)
            elif isinstance(field.default, str):
                ok = isinstance(value, str) and value != ""
            else:
                ok = isinstance(value, int | float) and not isinstance(value, bool)
            if ok:
                values[field.name] = value
        settings = cls(**values)
        return replace(
            settings,
            new_opacity=clamp_opacity(settings.new_opacity),
            theme=settings.theme if settings.theme in THEMES else THEMES[0],
            language=settings.language if settings.language in LANGUAGES else LANGUAGES[0],
            hide_all_key=parse_key(data.get("hide_all_key")),
            hide_all_modifiers=canonical_modifiers(data.get("hide_all_modifiers")),
            characters=characters.from_json(data.get("characters")),
            timer_pauses=pauses_from_json(data.get("timer_pauses")),
            panel_rect=_panel_rect(data.get("panel_rect")),
        )


def _panel_rect(value: object) -> PanelRect | None:
    """[x, y, width, height] from settings.json, or None if it isn't one."""
    if not isinstance(value, list) or len(value) != 4:
        return None
    if not all(isinstance(n, int) and not isinstance(n, bool) for n in value):
        return None
    x, y, width, height = value
    return (x, y, width, height) if width > 0 and height > 0 else None


def load(path: Path) -> Settings:
    try:
        return Settings.from_json(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return Settings()


def save(path: Path, settings: Settings) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings.to_json(), indent=2), encoding="utf-8")
