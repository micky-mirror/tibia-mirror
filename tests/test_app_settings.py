"""Reading the new settings class from the content of settings.json."""

from tibia_mirror.settings.app_settings import AppSettings


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
            "autosave": True,
            "mirror_frame": False,
            "frame_tint": True,
            "rounded_corners": True,
            "fades": False,
        }
    )

    assert settings.is_profile_per_character_on
    assert settings.is_autosave_on
    assert not settings.is_mirror_frame_on
    assert settings.is_frame_tint_on
    assert settings.is_rounded_corners_on
    assert not settings.is_fade_on


def test_wrong_on_off_settings_become_the_defaults() -> None:
    settings = AppSettings.from_json({"autosave": 1, "mirror_frame": "no", "fades": None})

    assert settings == AppSettings()
