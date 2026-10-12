"""The store that holds the settings of the new app."""

from pathlib import Path

from tibia_mirror.settings.app_settings import AppSettings
from tibia_mirror.settings.app_settings_store import AppSettingsStore


def do_nothing() -> None:
    pass


def test_missing_file_gives_the_default_settings(tmp_path: Path) -> None:
    store = AppSettingsStore(tmp_path / "settings.json", do_nothing)

    assert store.current == AppSettings()


def test_broken_file_gives_the_default_settings(tmp_path: Path) -> None:
    file = tmp_path / "settings.json"
    file.write_text("{ this is not json", encoding="utf-8")

    assert AppSettingsStore(file, do_nothing).current == AppSettings()


def test_saved_settings_are_loaded(tmp_path: Path) -> None:
    file = tmp_path / "settings.json"
    file.write_text('{"theme": "light", "autosave": true}', encoding="utf-8")

    store = AppSettingsStore(file, do_nothing)

    assert store.current.theme == "light"
    assert store.current.is_autosave_on
