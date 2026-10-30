"""The store that holds the settings of the new app."""

from pathlib import Path

from tibia_mirror.settings.app_settings import AppSettings
from tibia_mirror.settings.app_settings_store import AppSettingsStore


def do_nothing(previous: AppSettings, current: AppSettings) -> None:
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
    file.write_text('{"theme": "light", "panel_on_top": true}', encoding="utf-8")

    store = AppSettingsStore(file, do_nothing)

    assert store.current.theme == "light"
    assert store.current.is_panel_on_top


def test_update_changes_the_settings_and_tells_the_app(tmp_path: Path) -> None:
    calls: list[tuple[AppSettings, AppSettings]] = []
    store = AppSettingsStore(
        tmp_path / "settings.json",
        lambda previous, current: calls.append((previous, current)),
    )
    settings_at_start = store.current

    store.update(theme="light", is_panel_on_top=True)

    assert store.current.theme == "light"
    assert store.current.is_panel_on_top
    assert calls == [(settings_at_start, store.current)]


def test_update_with_the_same_values_does_not_tell_the_app(tmp_path: Path) -> None:
    calls: list[tuple[AppSettings, AppSettings]] = []
    store = AppSettingsStore(
        tmp_path / "settings.json",
        lambda previous, current: calls.append((previous, current)),
    )

    store.update(theme=store.current.theme)

    assert calls == []


def test_a_listener_is_called_after_a_change_and_reads_the_new_settings(tmp_path: Path) -> None:
    store = AppSettingsStore(tmp_path / "settings.json", do_nothing)
    seen_themes: list[str] = []
    store.add_listener(lambda: seen_themes.append(store.current.theme))

    store.update(theme="light")

    assert seen_themes == ["light"]


def test_a_listener_is_called_after_the_app(tmp_path: Path) -> None:
    calls: list[str] = []
    store = AppSettingsStore(
        tmp_path / "settings.json",
        lambda previous, current: calls.append("app"),
    )
    store.add_listener(lambda: calls.append("listener"))

    store.update(theme="light")

    assert calls == ["app", "listener"]


def test_a_listener_is_not_called_when_nothing_changed(tmp_path: Path) -> None:
    store = AppSettingsStore(tmp_path / "settings.json", do_nothing)
    calls: list[str] = []
    store.add_listener(lambda: calls.append("listener"))

    store.update(theme=store.current.theme)

    assert calls == []


def test_a_removed_listener_is_not_called(tmp_path: Path) -> None:
    store = AppSettingsStore(tmp_path / "settings.json", do_nothing)
    calls: list[str] = []

    def listener() -> None:
        calls.append("listener")

    store.add_listener(listener)
    store.remove_listener(listener)

    store.update(theme="light")

    assert calls == []


def test_a_listener_can_remove_itself_while_the_others_are_called(tmp_path: Path) -> None:
    store = AppSettingsStore(tmp_path / "settings.json", do_nothing)
    calls: list[str] = []

    def first_listener() -> None:
        calls.append("first")
        store.remove_listener(first_listener)

    store.add_listener(first_listener)
    store.add_listener(lambda: calls.append("second"))

    store.update(theme="light")

    assert calls == ["first", "second"]


def test_save_writes_what_the_next_store_loads(tmp_path: Path) -> None:
    file = tmp_path / "settings.json"
    store = AppSettingsStore(file, do_nothing)
    store.update(theme="light", hide_all_key=(120, ("shift",)))

    store.save()

    assert AppSettingsStore(file, do_nothing).current == store.current


def test_save_creates_the_folder_of_the_file(tmp_path: Path) -> None:
    file = tmp_path / "new folder" / "settings.json"

    AppSettingsStore(file, do_nothing).save()

    assert file.exists()
