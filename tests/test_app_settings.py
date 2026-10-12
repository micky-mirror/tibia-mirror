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
