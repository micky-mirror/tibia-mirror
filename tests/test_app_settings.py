"""Reading the settings from the content of settings.json, and writing them back."""

import json
from typing import get_type_hints

from tibia_mirror.config import DEFAULT_OPACITY, MIN_OPACITY
from tibia_mirror.settings.app_settings import AppSettings, AppSettingsUpdate

# Settings where every value is different from its default.
CHANGED_SETTINGS = AppSettings(
    theme="light",
    language="pl",
    is_panel_on_top=True,
    is_profile_per_character_on=True,
    new_mirror_opacity=0.8,
    is_mirror_frame_on=False,
    is_frame_tint_on=True,
    is_rounded_corners_on=True,
    last_profile="Knight",
    last_character="Bubble",
    hide_all_key=(120, ("ctrl", "shift")),
    panel_rect=(-300, 50, 400, 600),
    timer_pauses=(("Bubble", "mirror-1", 12.5),),
)
# settings.json as v1.0.0 writes CHANGED_SETTINGS
V1_FILE_CONTENT = {
    "autosave": False,
    "new_opacity": 0.8,
    "mirror_frame": False,
    "fades": True,
    "panel_on_top": True,
    "rounded_corners": True,
    "frame_tint": True,
    "theme": "light",
    "language": "pl",
    "profile": "Knight",
    "profile_per_character": True,
    "characters": {},
    "timer_pauses": {"Bubble": {"mirror-1": 12.5}},
    "last_character": "Bubble",
    "hide_all_key": 120,
    "hide_all_modifiers": ["ctrl", "shift"],
    "panel_rect": [-300, 50, 400, 600],
}
# only v1.0.0 has fade animations, the autosave setting and character links
V1_ONLY_KEYS = ("autosave", "fades", "characters")


def test_empty_file_content_gives_the_defaults() -> None:
    assert AppSettings.from_json({}) == AppSettings()


def test_content_that_is_not_an_object_gives_the_defaults() -> None:
    assert AppSettings.from_json([1, 2]) == AppSettings()


def test_saved_theme_and_language_are_read() -> None:
    settings = AppSettings.from_json({"theme": "light", "language": "pl"})

    assert settings.theme == "light"
    assert settings.language == "pl"


def test_wrong_theme_and_language_become_the_first_choice() -> None:
    settings = AppSettings.from_json({"theme": "pink", "language": 5})

    assert settings == AppSettings()


def test_saved_panel_on_top_is_read() -> None:
    settings = AppSettings.from_json({"panel_on_top": True})

    assert settings.is_panel_on_top


def test_wrong_panel_on_top_becomes_the_default() -> None:
    settings = AppSettings.from_json({"panel_on_top": "yes"})

    assert not settings.is_panel_on_top


def test_saved_on_off_settings_are_read() -> None:
    settings = AppSettings.from_json(
        {
            "profile_per_character": True,
            "mirror_frame": False,
            "frame_tint": True,
            "rounded_corners": True,
        }
    )

    assert settings.is_profile_per_character_on
    assert not settings.is_mirror_frame_on
    assert settings.is_frame_tint_on
    assert settings.is_rounded_corners_on


def test_wrong_on_off_settings_become_the_defaults() -> None:
    settings = AppSettings.from_json(
        {"profile_per_character": 1, "mirror_frame": "no", "frame_tint": None}
    )

    assert settings == AppSettings()


def test_saved_opacity_of_new_mirrors_is_read() -> None:
    settings = AppSettings.from_json({"new_opacity": 0.8})

    assert settings.new_mirror_opacity == 0.8


def test_opacity_outside_the_range_is_moved_into_it() -> None:
    assert AppSettings.from_json({"new_opacity": 0}).new_mirror_opacity == MIN_OPACITY
    assert AppSettings.from_json({"new_opacity": 7}).new_mirror_opacity == 1.0


def test_wrong_opacity_becomes_the_default() -> None:
    assert AppSettings.from_json({"new_opacity": True}).new_mirror_opacity == DEFAULT_OPACITY
    assert AppSettings.from_json({"new_opacity": "half"}).new_mirror_opacity == DEFAULT_OPACITY


def test_saved_profile_and_character_are_read() -> None:
    settings = AppSettings.from_json({"profile": "Knight", "last_character": "Bubble"})

    assert settings.last_profile == "Knight"
    assert settings.last_character == "Bubble"


def test_wrong_profile_and_character_become_the_defaults() -> None:
    settings = AppSettings.from_json({"profile": "", "last_character": 12})

    assert settings == AppSettings()


def test_saved_hide_all_key_is_read_with_its_modifiers() -> None:
    data = {"hide_all_key": 120, "hide_all_modifiers": ["shift", "ctrl"]}

    assert AppSettings.from_json(data).hide_all_key == (120, ("ctrl", "shift"))


def test_saved_hide_all_key_without_modifiers_is_read() -> None:
    assert AppSettings.from_json({"hide_all_key": 120}).hide_all_key == (120, ())


def test_missing_or_wrong_hide_all_key_means_no_key() -> None:
    assert AppSettings.from_json({"hide_all_modifiers": ["ctrl"]}).hide_all_key is None
    assert AppSettings.from_json({"hide_all_key": "F9"}).hide_all_key is None


def test_saved_panel_place_is_read() -> None:
    settings = AppSettings.from_json({"panel_rect": [-300, 50, 400, 600]})

    assert settings.panel_rect == (-300, 50, 400, 600)


def test_wrong_panel_place_means_no_saved_place() -> None:
    wrong_values = (
        "100,50,400,600",  # not a list
        [100, 50, 400],  # too short
        [100, 50, 400.5, 600],  # not a whole number
        [True, 50, 400, 600],  # true is not a number here
        [100, 50, 0, 600],  # no width
    )

    for value in wrong_values:
        assert AppSettings.from_json({"panel_rect": value}).panel_rect is None


def test_saved_timer_pauses_are_read() -> None:
    data = {"timer_pauses": {"Bubble": {"mirror-1": 12.5, "mirror-2": "long"}}}

    assert AppSettings.from_json(data).timer_pauses == (("Bubble", "mirror-1", 12.5),)


def test_written_settings_are_read_back_the_same() -> None:
    file_content = json.loads(json.dumps(CHANGED_SETTINGS.to_json()))

    assert AppSettings.from_json(file_content) == CHANGED_SETTINGS


def test_written_default_settings_are_read_back_the_same() -> None:
    file_content = json.loads(json.dumps(AppSettings().to_json()))

    assert AppSettings.from_json(file_content) == AppSettings()


def test_a_settings_file_of_v1_0_0_is_read() -> None:
    assert AppSettings.from_json(V1_FILE_CONTENT) == CHANGED_SETTINGS


def test_written_settings_keep_the_format_of_v1_0_0() -> None:
    shared_content = {
        key: value for key, value in V1_FILE_CONTENT.items() if key not in V1_ONLY_KEYS
    }

    assert CHANGED_SETTINGS.to_json() == shared_content


def test_update_type_has_every_setting_with_the_same_type() -> None:
    assert get_type_hints(AppSettingsUpdate) == get_type_hints(AppSettings)
